# Copy this file to pipeline.local.ps1 and replace the example upload jobs with your private paths and chat IDs.
$projectPath = (Resolve-Path (Join-Path $PSScriptRoot ".")).Path
Set-Location -Path $projectPath

$venvPython = Join-Path $projectPath "venv\Scripts\python.exe"
if (-Not (Test-Path $venvPython)) {
    Write-Host "Error: virtual environment not found at $venvPython" -ForegroundColor Red
    exit 1
}

$uploads = [ordered]@{
    "C:\Path\To\First\Folder" = "<destination-chat-id>"
}

foreach ($folder in $uploads.Keys) {
    $channelId = $uploads[$folder]
    if (-Not (Test-Path $folder -PathType Container)) {
        Write-Host "Folder not found: $folder" -ForegroundColor Red
        exit 1
    }

    Write-Host "Starting upload for $folder..." -ForegroundColor Cyan
    & $venvPython (Join-Path $projectPath "main.py") $folder $channelId
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Upload stopped. Remaining jobs will not run." -ForegroundColor Red
        exit $LASTEXITCODE
    }
}

Write-Host "Process completed!" -ForegroundColor Green
