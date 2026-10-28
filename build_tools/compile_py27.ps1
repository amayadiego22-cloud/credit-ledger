[CmdletBinding(DefaultParameterSetName = 'Single')]
param(
    [Parameter(Mandatory = $true)][string]$PythonDll,
    [Parameter(Mandatory = $true, ParameterSetName = 'Single')][string]$Source,
    [Parameter(Mandatory = $true, ParameterSetName = 'Single')][string]$Output,
    [Parameter(ParameterSetName = 'Single')][string]$Filename,
    [Parameter(Mandatory = $true, ParameterSetName = 'Batch')][string]$Manifest,
    [Parameter(Mandatory = $true, ParameterSetName = 'Test')][switch]$SelfTest
)

# Invoke with powershell.exe -NoProfile -File or pwsh -NoProfile -File.
# This script owns one native interpreter in that short-lived child process.
$ErrorActionPreference = 'Stop'
if (-not [Environment]::Is64BitProcess) {
    throw 'Use a 64-bit PowerShell process for the game win64/python27.dll.'
}
$dllPath = (Get-Item -LiteralPath $PythonDll).FullName
$homePath = Join-Path $PSScriptRoot 'runtime_home'
[IO.Directory]::CreateDirectory($homePath) | Out-Null

Add-Type -Path (Join-Path $PSScriptRoot 'Python27Compiler.cs')
$compiler = New-Object WotEconomy.Build.Python27Compiler($dllPath, $homePath)
try {
    if ($SelfTest) {
        $testDir = Join-Path $PSScriptRoot 'selftest with spaces'
        [IO.Directory]::CreateDirectory($testDir) | Out-Null
        $samplePath = Join-Path $testDir 'sample own source.py'
        $samplePyc = Join-Path $testDir 'sample own source.pyc'
        $sample = @'
# -*- coding: utf-8 -*-
import sys
assert sys.version_info[:2] == (2, 7)
assert sys.path == []
assert 'site' not in sys.modules
assert sys.dont_write_bytecode
meta = 1000000L
neto = 120000 - (15000 + 10000 + 5000)
assert meta == long('1000000')
assert neto == 90000
texto = u'__ACCENTED_CREDITS__: 1.000.000'
assert texto[:8] == u'cr\u00e9ditos'
assert texto.endswith(u'1.000.000')
'@
        $sample = $sample.Replace('__ACCENTED_CREDITS__', ('cr' + [char]0xe9 + 'ditos'))
        [IO.File]::WriteAllText($samplePath, $sample + "`n", (New-Object Text.UTF8Encoding($false)))
        $result = $compiler.Compile($samplePath, $samplePyc, 'selftest with spaces/sample own source.py', $true)
        $result | ConvertTo-Json -Compress
    }
    elseif ($PSCmdlet.ParameterSetName -eq 'Batch') {
        $jobs = Get-Content -LiteralPath $Manifest -Raw -Encoding UTF8 | ConvertFrom-Json
        foreach ($job in $jobs) {
            if (-not $job.source -or -not $job.output) {
                throw 'Every manifest item requires source and output.'
            }
            $logicalName = $job.filename
            if (-not $logicalName) { $logicalName = [IO.Path]::GetFileName($job.source) }
            $compiler.Compile([string]$job.source, [string]$job.output, [string]$logicalName, $false) | ConvertTo-Json -Compress
        }
    }
    else {
        if (-not $Filename) { $Filename = [IO.Path]::GetFileName($Source) }
        $compiler.Compile($Source, $Output, $Filename, $false) | ConvertTo-Json -Compress
    }
}
finally {
    $compiler.Dispose()
}
