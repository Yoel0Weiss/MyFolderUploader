Set-ExecutionPolicy -Scope Process Bypass -Force
Set-Location "C:\Users\My Computer\Documents\MyFolderUploader"
& ".\venv\Scripts\Activate.ps1"
python ".\main.py"