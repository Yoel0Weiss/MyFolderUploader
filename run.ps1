Set-ExecutionPolicy -Scope Process Bypass -Force
$projectPath = (Resolve-Path (Join-Path $PSScriptRoot ".")).Path
Set-Location -Path $projectPath
& (Join-Path $projectPath "venv\Scripts\Activate.ps1")
python (Join-Path $projectPath "main.py")
