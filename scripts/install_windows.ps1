param([string]$FontDirectory = $PSScriptRoot)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$OutputEncoding = [Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)

function Get-GenZuiFontRegistration([string]$Path, [string]$Name) {
    # New-Item -Force resets an existing registry key, including other fonts.
    if (!(Test-Path -LiteralPath $Path)) {
        New-Item -Path $Path | Out-Null
    }
    $property = (Get-ItemProperty -LiteralPath $Path).PSObject.Properties[$Name]
    if ($property) { [string]$property.Value }
}

# Each face ships with its own validation report.
$faces = @(
    @{ Style = 'Regular'; File = 'GenZuiSerif-Regular.ttf'; Report = 'checks.json'; Weight = 'Normal' },
    @{ Style = 'Bold'; File = 'GenZuiSerif-Bold.ttf'; Report = 'checks-bold.json'; Weight = 'Bold' }
)
foreach ($face in $faces) {
    $checks = Get-Content -LiteralPath (Join-Path $FontDirectory $face.Report) -Raw | ConvertFrom-Json
    if ($checks.status -ne 'passed' -or $checks.family -ne 'GenZui Serif') {
        throw "The GenZui $($face.Style) validation report is missing or does not match this family."
    }
    $version = [regex]::Match($checks.font_version, '^Version ([0-9]+\.[0-9]+)$')
    if (!$version.Success) { throw "The $($face.Style) validation report has an invalid font version." }
    $face.Version = $checks.font_version
    $face.Expected = $checks.ttf_sha256
    $face.Source = Join-Path $FontDirectory $face.File
    if ((Get-FileHash -LiteralPath $face.Source -Algorithm SHA256).Hash.ToLowerInvariant() -ne $face.Expected) {
        throw "The $($face.Style) font checksum does not match its validation report."
    }
    # A revision can be rebuilt during outline development. A content suffix
    # keeps a new build separate from font files held open by applications.
    $face.Stem = [IO.Path]::GetFileNameWithoutExtension($face.File)
    $face.InstalledName = $face.Stem + '-' + $version.Groups[1].Value + '-' + $face.Expected.Substring(0, 12) + '.ttf'
    $face.Entry = "GenZui Serif $($face.Style) (TrueType)"
}

Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class GenZuiFontInstall {
    [DllImport("gdi32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    public static extern int AddFontResourceEx(string path, uint flags, IntPtr reserved);
    [DllImport("gdi32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    public static extern bool RemoveFontResourceEx(string path, uint flags, IntPtr reserved);
    [DllImport("user32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    public static extern IntPtr SendMessageTimeout(IntPtr hwnd, uint msg, UIntPtr wParam,
        IntPtr lParam, uint flags, uint timeout, out UIntPtr result);
}
'@

$folder = Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) 'Microsoft\Windows\Fonts'
$key = 'HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Fonts'
New-Item -ItemType Directory -Path $folder -Force | Out-Null
foreach ($face in $faces) {
    $face.Destination = Join-Path $folder $face.InstalledName
    $face.Previous = Get-GenZuiFontRegistration -Path $key -Name $face.Entry
    $same = (Test-Path -LiteralPath $face.Destination) -and (
        (Get-FileHash -LiteralPath $face.Destination -Algorithm SHA256).Hash.ToLowerInvariant() -eq $face.Expected)
    if (!$same) {
        Copy-Item -LiteralPath $face.Source -Destination $face.Destination -Force
    }
}
# The faces are registered as one family. If any registration fails, every face
# changed so far returns to its previous registration.
$changed = @()
try {
    foreach ($face in $faces) {
        # Stage the new version before changing registration. Open applications can
        # keep their old file handles while newly started applications see the update.
        if ($face.Previous -and $face.Previous -ne $face.Destination -and (Test-Path -LiteralPath $face.Previous)) {
            while ([GenZuiFontInstall]::RemoveFontResourceEx($face.Previous, 0, [IntPtr]::Zero)) { }
        }
        $changed += $face
        New-ItemProperty -Path $key -Name $face.Entry -PropertyType String -Value $face.Destination -Force | Out-Null
        $face.Added = [GenZuiFontInstall]::AddFontResourceEx($face.Destination, 0, [IntPtr]::Zero)
        if ($face.Added -eq 0) {
            throw "Windows could not register the new $($face.Style) font resource."
        }
    }
} catch {
    foreach ($face in $changed) {
        if ($face.Previous -ne $face.Destination) {
            [void][GenZuiFontInstall]::RemoveFontResourceEx($face.Destination, 0, [IntPtr]::Zero)
        }
        if ($face.Previous) {
            New-ItemProperty -Path $key -Name $face.Entry -PropertyType String -Value $face.Previous -Force | Out-Null
            [void][GenZuiFontInstall]::AddFontResourceEx($face.Previous, 0, [IntPtr]::Zero)
        } else {
            Remove-ItemProperty -Path $key -Name $face.Entry -ErrorAction SilentlyContinue
        }
    }
    throw
}
[UIntPtr]$result = [UIntPtr]::Zero
[void][GenZuiFontInstall]::SendMessageTimeout([IntPtr]0xffff, 0x001D, [UIntPtr]::Zero,
    [IntPtr]::Zero, 2, 3000, [ref]$result)
foreach ($face in $faces) {
    if ((Get-FileHash -LiteralPath $face.Destination -Algorithm SHA256).Hash.ToLowerInvariant() -ne $face.Expected) {
        throw "Installed $($face.Style) font verification failed."
    }
    if ((Get-ItemPropertyValue -Path $key -Name $face.Entry) -ne $face.Destination) {
        throw "$($face.Style) font registration verification failed."
    }
}
# GDI+ can retain the font list from before installation. Verify discovery in
# a fresh process, as an application started after installation would do.
$probe = @'
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName PresentationCore
$fonts = New-Object System.Drawing.Text.InstalledFontCollection
try {
    $family = @($fonts.Families | Where-Object { $_.GetName(1033) -eq 'GenZui Serif' })
    if (!$family.Count) { throw 'GenZui Serif is not visible in the Windows font collection.' }
    $resolved = @{}
    foreach ($style in 'Regular', 'Bold') {
        $weight = if ($style -eq 'Bold') { [System.Windows.FontWeights]::Bold } else { [System.Windows.FontWeights]::Normal }
        $face = [System.Windows.Media.Typeface]::new([System.Windows.Media.FontFamily]::new('GenZui Serif'),
            [System.Windows.FontStyles]::Normal, $weight, [System.Windows.FontStretches]::Normal)
        [System.Windows.Media.GlyphTypeface]$glyphFace = $null
        if (!$face.TryGetGlyphTypeface([ref]$glyphFace)) {
            throw "Windows could not resolve the installed GenZui $style glyph face."
        }
        # Without a registered Bold, Windows emboldens Regular instead.
        if ($glyphFace.StyleSimulations -ne [System.Windows.Media.StyleSimulations]::None) {
            throw "Windows simulates GenZui Serif $style instead of using the installed face."
        }
        $resolved[$style] = (Get-FileHash -LiteralPath $glyphFace.FontUri.LocalPath -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    $data = @{family=$family[0].GetName(1033);family_ja=$family[0].GetName(1041);resolved=$resolved} | ConvertTo-Json -Compress
    [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($data))
} finally { $fonts.Dispose() }
'@
$encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($probe))
$shell = (Get-Process -Id $PID).Path
$answer = & $shell -NoProfile -NonInteractive -EncodedCommand $encoded
if ($LASTEXITCODE -ne 0) { throw 'Fresh-process font verification failed.' }
$names = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($answer)) | ConvertFrom-Json
foreach ($face in $faces) {
    if ($names.resolved.($face.Style) -ne $face.Expected) {
        throw "Windows resolved a different $($face.Style) font version. Registration is updated; restart applications and run the installer again."
    }
}
foreach ($face in $faces) {
    $face.PreviousRemoved = $false
    if ($face.Previous -and $face.Previous -ne $face.Destination -and
        [IO.Path]::GetDirectoryName($face.Previous) -eq $folder -and
        [IO.Path]::GetFileName($face.Previous) -match ('^' + $face.Stem + '(?:-[0-9]+\.[0-9]+(?:-[0-9a-f]{12})?)?\.ttf$') -and
        (Test-Path -LiteralPath $face.Previous)) {
        try {
            Remove-Item -LiteralPath $face.Previous -Force -ErrorAction Stop
            $face.PreviousRemoved = $true
        } catch [System.IO.IOException] {
            # In-use old files can remain until the applications using them exit.
        } catch [System.UnauthorizedAccessException] {
            # Registration is already verified; cleanup can wait.
        }
    }
}
[ordered]@{
    family = $names.family
    family_ja = $names.family_ja
    installed = $true
    faces = @($faces | ForEach-Object {
        [ordered]@{
            style = $_.Style
            version = $_.Version
            sha256 = $_.Expected
            previous_file_removed = $_.PreviousRemoved
            added_resources = $_.Added
        }
    })
    registry_verified = $true
    windows_font_collection_verified = $true
    resolved_font_bytes_verified = $true
} | ConvertTo-Json -Depth 4
