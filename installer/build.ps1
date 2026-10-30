param(
    [string]$OutputDirectory = (Join-Path $PSScriptRoot '..\dist\installer'),
    [string]$PayloadPath = (Join-Path $PSScriptRoot '..\dist\local.credit_ledger.0.22.14.wotmod')
)
$ErrorActionPreference = 'Stop'
$installerSource = $PSScriptRoot
$installerOutput = [IO.Path]::GetFullPath($OutputDirectory)
$installerPayload = $PayloadPath
$installerPayload = [IO.Path]::GetFullPath($installerPayload)
if ((Get-FileHash -LiteralPath $installerPayload -Algorithm SHA256).Hash -ne '2A3659B911679EDC54AA59336C9761F7A9A5AC825D435464E9F01BD9A2C8BC17') { throw 'Payload hash mismatch' }
New-Item -ItemType Directory -Path $installerOutput -Force | Out-Null
$installerCompiler = Join-Path $env:WINDIR 'Microsoft.NET\Framework\v4.0.30319\csc.exe'
Add-Type -AssemblyName System.Drawing
$installerBitmap = New-Object Drawing.Bitmap 48,48
$installerGraphics = [Drawing.Graphics]::FromImage($installerBitmap)
$installerGraphics.SmoothingMode = [Drawing.Drawing2D.SmoothingMode]::AntiAlias
$installerGraphics.Clear([Drawing.Color]::FromArgb(16,21,25))
$installerPen = New-Object Drawing.Pen ([Drawing.Color]::FromArgb(218,186,100)),3
$installerGraphics.DrawEllipse($installerPen,5,5,37,37)
$installerBrush = New-Object Drawing.SolidBrush ([Drawing.Color]::FromArgb(218,186,100))
$installerGraphics.FillRectangle($installerBrush,14,25,5,10)
$installerGraphics.FillRectangle($installerBrush,22,19,5,16)
$installerGraphics.FillRectangle($installerBrush,30,13,5,22)
$installerIcon = [Drawing.Icon]::FromHandle($installerBitmap.GetHicon())
$installerIconPath = Join-Path $installerOutput 'credit-ledger.ico'
$installerStream = [IO.File]::Create($installerIconPath)
$installerIcon.Save($installerStream)
$installerStream.Dispose(); $installerGraphics.Dispose(); $installerBitmap.Dispose(); $installerPen.Dispose(); $installerBrush.Dispose()
$installerExecutable = Join-Path $installerOutput 'CreditLedger-Setup-0.22.14.exe'
$installerReferences = @('/r:System.dll','/r:System.Core.dll','/r:System.Xml.dll','/r:System.IO.Compression.dll','/r:System.IO.Compression.FileSystem.dll')
$installerArgs = @('/nologo','/target:winexe','/platform:anycpu','/optimize+',('/out:' + $installerExecutable),('/win32manifest:' + (Join-Path $installerSource 'installer.manifest')),('/win32icon:' + $installerIconPath),('/resource:' + $installerPayload + ',CreditLedger.Payload'),('/resource:' + $installerIconPath + ',CreditLedger.Icon'),'/r:System.Drawing.dll','/r:System.Windows.Forms.dll') + $installerReferences + @((Join-Path $installerSource 'InstallerEngine.cs'),(Join-Path $installerSource 'InstallerForm.cs'))
& $installerCompiler @installerArgs
if ($LASTEXITCODE -ne 0) { throw 'Installer compilation failed' }
$installerTestExecutable = Join-Path $installerOutput 'InstallerTests.exe'
$installerTestArgs = @('/nologo','/target:exe','/platform:anycpu','/optimize+',('/out:' + $installerTestExecutable),('/resource:' + $installerPayload + ',CreditLedger.Payload')) + $installerReferences + @((Join-Path $installerSource 'InstallerEngine.cs'),(Join-Path $installerSource 'InstallerTests.cs'))
& $installerCompiler @installerTestArgs
if ($LASTEXITCODE -ne 0) { throw 'Test compilation failed' }
$installerFixtures = Join-Path $installerOutput ('qa-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path (Join-Path $installerFixtures 'link-target') -Force | Out-Null
New-Item -ItemType Junction -Path (Join-Path $installerFixtures 'linked-game') -Target (Join-Path $installerFixtures 'link-target') | Out-Null
& $installerTestExecutable $installerFixtures | Tee-Object -FilePath (Join-Path $installerOutput 'tests.log')
if ($LASTEXITCODE -ne 0) { throw 'Installer tests failed' }
$installerEngineSummary = [regex]::Match((Get-Content -LiteralPath (Join-Path $installerOutput 'tests.log') -Raw), 'TOTAL (\d+) passed')
if (-not $installerEngineSummary.Success) { throw 'Installer engine test summary missing' }
$installerEngineCount = [int]$installerEngineSummary.Groups[1].Value
if ($installerEngineCount -lt 1) { throw 'No installer engine checks passed' }
$installerFlowExecutable = Join-Path $installerOutput 'InstallerFlowTests.exe'
$installerFlowArgs = @('/nologo','/target:exe','/platform:anycpu','/optimize+','/main:CreditLedgerSetup.InstallerFlowTests',('/out:' + $installerFlowExecutable),('/resource:' + $installerPayload + ',CreditLedger.Payload'),('/resource:' + $installerIconPath + ',CreditLedger.Icon'),'/r:System.Drawing.dll','/r:System.Windows.Forms.dll') + $installerReferences + @((Join-Path $installerSource 'InstallerEngine.cs'),(Join-Path $installerSource 'InstallerForm.cs'),(Join-Path $installerSource 'InstallerFlowTests.cs'))
& $installerCompiler @installerFlowArgs
if ($LASTEXITCODE -ne 0) { throw 'Installer flow test compilation failed' }
$installerFlowLog = Join-Path $installerOutput 'flow-tests.log'
& $installerFlowExecutable | Tee-Object -FilePath $installerFlowLog
if ($LASTEXITCODE -ne 0) { throw 'Installer flow tests failed' }
$installerFlowSummary = [regex]::Match((Get-Content -LiteralPath $installerFlowLog -Raw), '(\d+) form-flow checks passed')
if (-not $installerFlowSummary.Success) { throw 'Installer flow test summary missing' }
$installerFlowCount = [int]$installerFlowSummary.Groups[1].Value
if ($installerFlowCount -lt 1) { throw 'No installer flow checks passed' }
Get-FileHash -LiteralPath $installerExecutable -Algorithm SHA256 | Select-Object Path,Hash | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $installerOutput 'sha256.json') -Encoding UTF8
$installerHash = (Get-FileHash -LiteralPath $installerExecutable -Algorithm SHA256).Hash.ToLowerInvariant()
($installerHash + '  ' + [IO.Path]::GetFileName($installerExecutable)) | Set-Content -LiteralPath (Join-Path $installerOutput 'SHA256SUMS.txt') -Encoding ASCII
foreach ($installerGuide in @('LEEME-INSTALADOR.txt','INSTALLER-README.txt')) {
    Copy-Item -LiteralPath (Join-Path $installerSource $installerGuide) -Destination (Join-Path $installerOutput $installerGuide) -Force
}
$installerZip = Join-Path $installerOutput 'CreditLedger-Installer-0.22.14-Windows.zip'
Compress-Archive -LiteralPath @($installerExecutable, (Join-Path $installerOutput 'LEEME-INSTALADOR.txt'), (Join-Path $installerOutput 'INSTALLER-README.txt'), (Join-Path $installerOutput 'SHA256SUMS.txt')) -DestinationPath $installerZip -Force
@{
    installer='0.22.14'; file_version='0.22.14.3'; installer_revision=3; mod='0.22.14'; supported_clients=@('2.4.1.0','2.4.1.1'); regions=@('NA','EU','ASIA');
    executable=[IO.Path]::GetFileName($installerExecutable); executable_sha256=$installerHash;
    payload_sha256='2a3659b911679edc54aa59336c9761f7a9a5ac825d435464e9f01bd9a2c8bc17';
    archive=[IO.Path]::GetFileName($installerZip); archive_sha256=(Get-FileHash -LiteralPath $installerZip -Algorithm SHA256).Hash.ToLowerInvariant();
    automated_tests_passed=$installerEngineCount; engine_tests_passed=$installerEngineCount; form_flow_tests_passed=$installerFlowCount; test_fixture_directory=$installerFixtures; public_archive_entries=4;
    digitally_signed=$false; uploaded_to_wgmods=$false; existing_player_data_modified=$false
} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $installerOutput 'build-receipt.json') -Encoding UTF8
Write-Output $installerExecutable
