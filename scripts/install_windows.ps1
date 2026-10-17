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

$fontName = 'GenZuiSerif-Regular.ttf'
$source = Join-Path $FontDirectory $fontName
$checks = Get-Content -LiteralPath (Join-Path $FontDirectory 'checks.json') -Raw | ConvertFrom-Json
if ($checks.status -ne 'passed' -or $checks.family -ne 'GenZui Serif') {
    throw 'The GenZui validation report is missing or does not match this family.'
}
$expected = $checks.ttf_sha256
$version = [regex]::Match($checks.font_version, '^Version ([0-9]+\.[0-9]+)$')
if (!$version.Success) { throw 'The validation report has an invalid font version.' }
if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected) {
    throw 'The font checksum does not match the validation report.'
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
# A revision can be rebuilt during outline development. A content suffix
# keeps a new build separate from font files held open by applications.
$installedName = 'GenZuiSerif-Regular-' + $version.Groups[1].Value + '-' + $expected.Substring(0, 12) + '.ttf'
$destination = Join-Path $folder $installedName
$key = 'HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Fonts'
$entry = 'GenZui Serif Regular (TrueType)'
New-Item -ItemType Directory -Path $folder -Force | Out-Null
$previous = Get-GenZuiFontRegistration -Path $key -Name $entry
$same = (Test-Path -LiteralPath $destination) -and (
    (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant() -eq $expected)
if (!$same) {
    Copy-Item -LiteralPath $source -Destination $destination -Force
}
# Stage the new version before changing registration. Open applications can
# keep their old file handles while newly started applications see the update.
if ($previous -and $previous -ne $destination -and (Test-Path -LiteralPath $previous)) {
    while ([GenZuiFontInstall]::RemoveFontResourceEx($previous, 0, [IntPtr]::Zero)) { }
}
New-ItemProperty -Path $key -Name $entry -PropertyType String -Value $destination -Force | Out-Null
$added = [GenZuiFontInstall]::AddFontResourceEx($destination, 0, [IntPtr]::Zero)
if ($added -eq 0) {
    if ($previous) {
        New-ItemProperty -Path $key -Name $entry -PropertyType String -Value $previous -Force | Out-Null
        [void][GenZuiFontInstall]::AddFontResourceEx($previous, 0, [IntPtr]::Zero)
    } else {
        Remove-ItemProperty -Path $key -Name $entry -ErrorAction SilentlyContinue
    }
    throw 'Windows could not register the new font resource.'
}
[UIntPtr]$result = [UIntPtr]::Zero
[void][GenZuiFontInstall]::SendMessageTimeout([IntPtr]0xffff, 0x001D, [UIntPtr]::Zero,
    [IntPtr]::Zero, 2, 3000, [ref]$result)
if ((Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected) {
    throw 'Installed font verification failed.'
}
if ((Get-ItemPropertyValue -Path $key -Name $entry) -ne $destination) {
    throw 'Font registration verification failed.'
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
    if (!$family.Count -or !$family[0].IsStyleAvailable([Drawing.FontStyle]::Regular)) {
        throw 'GenZui Serif Regular is not visible in the Windows font collection.'
    }
    $face = [System.Windows.Media.Typeface]::new('GenZui Serif')
    [System.Windows.Media.GlyphTypeface]$glyphFace = $null
    if (!$face.TryGetGlyphTypeface([ref]$glyphFace)) {
        throw 'Windows could not resolve the installed GenZui glyph face.'
    }
    $resolvedHash = (Get-FileHash -LiteralPath $glyphFace.FontUri.LocalPath -Algorithm SHA256).Hash.ToLowerInvariant()
    $data = @{family=$family[0].GetName(1033);family_ja=$family[0].GetName(1041);resolved_sha256=$resolvedHash} | ConvertTo-Json -Compress
    [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($data))
} finally { $fonts.Dispose() }
'@
$encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($probe))
$shell = (Get-Process -Id $PID).Path
$answer = & $shell -NoProfile -NonInteractive -EncodedCommand $encoded
if ($LASTEXITCODE -ne 0) { throw 'Fresh-process font verification failed.' }
$names = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($answer)) | ConvertFrom-Json
if ($names.resolved_sha256 -ne $expected) {
    throw 'Windows resolved a different font version. Registration is updated; restart applications and run the installer again.'
}
$oldFileRemoved = $false
if ($previous -and $previous -ne $destination -and
    [IO.Path]::GetDirectoryName($previous) -eq $folder -and
    [IO.Path]::GetFileName($previous) -match '^GenZuiSerif-Regular(?:-[0-9]+\.[0-9]+(?:-[0-9a-f]{12})?)?\.ttf$' -and
    (Test-Path -LiteralPath $previous)) {
    try {
        Remove-Item -LiteralPath $previous -Force -ErrorAction Stop
        $oldFileRemoved = $true
    } catch [System.IO.IOException] {
        # In-use old files can remain until the applications using them exit.
    } catch [System.UnauthorizedAccessException] {
        # Registration is already verified; cleanup can wait.
    }
}
[ordered]@{
    family = $names.family
    family_ja = $names.family_ja
    installed = $true
    version = $checks.font_version
    sha256 = $expected
    registry_verified = $true
    windows_font_collection_verified = $true
    resolved_font_bytes_verified = $true
    previous_file_removed = $oldFileRemoved
    added_resources = $added
} | ConvertTo-Json
