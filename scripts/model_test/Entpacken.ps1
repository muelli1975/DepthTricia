$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression.FileSystem
$target = Join-Path $PSScriptRoot 'DepthTricia-Test'
if (Test-Path $target) { throw "Ordner existiert bereits: $target. DepthTricia.exe dort starten oder in einen neuen Ordner entpacken." }
$stage = Join-Path $PSScriptRoot ("DepthTricia-Temp-" + [Guid]::NewGuid())
$archives = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'SHA256.json') -Raw | ConvertFrom-Json
try {
    foreach ($entry in $archives.psobject.Properties) {
        $file = Join-Path $PSScriptRoot $entry.Name
        Write-Host "Pruefe und entpacke $($entry.Name) ..."
        if ((Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash -ne $entry.Value) { throw "SHA-256: $file" }
        [IO.Compression.ZipFile]::ExtractToDirectory($file, $stage)
    }
    [IO.Directory]::Move($stage, $target)
    Write-Host "Fertig. DepthTricia.exe liegt in $target"
    Start-Process (Join-Path $target 'DepthTricia.exe')
} finally {
    if (Test-Path $stage) { Remove-Item -LiteralPath $stage -Recurse -Force }
}
