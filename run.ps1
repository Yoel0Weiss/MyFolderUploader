Set-ExecutionPolicy -Scope Process Bypass -Force
Set-Location "C:\Users\My Computer\Documents\TelegramBulkDirectoryUploader"
& ".\venv\Scripts\Activate.ps1"
python ".\main.py"