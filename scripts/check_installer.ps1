param([string]$Installer = (Join-Path $PSScriptRoot 'install_windows.ps1'))
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

# Run the installer's registry helper against a disposable key. No font
# resources or real font registrations are changed by this check.
$tokens = $null
$errors = $null
$ast = [Management.Automation.Language.Parser]::ParseFile($Installer, [ref]$tokens, [ref]$errors)
if ($errors.Count) { throw 'Installer PowerShell syntax check failed.' }
$helper = $ast.Find({
    param($node)
    $node -is [Management.Automation.Language.FunctionDefinitionAst] -and
        $node.Name -eq 'Get-GenZuiFontRegistration'
}, $true)
if (!$helper) { throw 'Installer registry helper is missing.' }
. ([scriptblock]::Create($helper.Extent.Text))

$key = 'HKCU:\Software\GenZuiInstallerTest-' + [guid]::NewGuid().ToString('N')
$passed = 0
try {
    $value = Get-GenZuiFontRegistration -Path $key -Name 'GenZui Serif Regular (TrueType)'
    if ($null -ne $value -or !(Test-Path -LiteralPath $key)) {
        throw 'First installation did not create an empty registration key.'
    }
    $passed++
    New-ItemProperty -LiteralPath $key -Name 'Existing font (TrueType)' -Value 'existing.ttf' -PropertyType String | Out-Null
    New-ItemProperty -LiteralPath $key -Name 'Existing binary value' -Value ([byte[]](1, 2, 3)) -PropertyType Binary | Out-Null
    New-Item -Path (Join-Path $key 'ExistingSubkey') | Out-Null
    $value = Get-GenZuiFontRegistration -Path $key -Name 'GenZui Serif Regular (TrueType)'
    if ($null -ne $value) { throw 'Missing font registration should return no value.' }
    $passed++
    New-ItemProperty -LiteralPath $key -Name 'GenZui Serif Regular (TrueType)' -Value 'previous.ttf' -PropertyType String | Out-Null
    $value = Get-GenZuiFontRegistration -Path $key -Name 'GenZui Serif Regular (TrueType)'
    if ($value -ne 'previous.ttf') { throw 'Existing font registration was not preserved.' }
    $passed++
    $item = Get-Item -LiteralPath $key
    if ($item.GetValue('Existing font (TrueType)') -ne 'existing.ttf' -or
        $item.GetValueKind('Existing binary value') -ne 'Binary' -or
        (($item.GetValue('Existing binary value')) -join ',') -ne '1,2,3' -or
        !(Test-Path -LiteralPath (Join-Path $key 'ExistingSubkey')) -or
        $item.ValueCount -ne 3) {
        throw 'Installer changed unrelated registry data.'
    }
    $passed++
    @{status='passed';registry_checks=$passed;installer_syntax='passed'} | ConvertTo-Json -Compress
} finally {
    if (Test-Path -LiteralPath $key) { Remove-Item -LiteralPath $key -Recurse -Force }
}
