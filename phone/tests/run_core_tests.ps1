$ErrorActionPreference = 'Stop'
$phoneRoot = Split-Path -Parent $PSScriptRoot
$corePath = Join-Path $phoneRoot 'unity/Week7PhoneCore.cs'
if (-not (Test-Path -LiteralPath $corePath)) { throw 'Week7PhoneCore.cs is missing' }
# The constructor is required by Unity's .NET Standard API; only .NET 9+ deprecates it.
Add-Type -Path $corePath, (Join-Path $PSScriptRoot 'CoreSelfTest.cs') -CompilerOptions '/nowarn:SYSLIB0057'
[CoreSelfTest]::Run().GetAwaiter().GetResult()
