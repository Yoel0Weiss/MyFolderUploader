# 1. Set the path to your project directory (where main.py and venv are located)
$projectPath = "C:\Users\My Computer\Documents\TelegramBulkDirectoryUploader"

# Navigate to the project directory to ensure relative paths (like .env or sessions) work correctly
Set-Location -Path $projectPath

# 2. Define the exact path to the Python executable inside the virtual environment
$venvPython = Join-Path $projectPath "venv\Scripts\python.exe"

# Verify that the virtual environment exists
if (-Not (Test-Path $venvPython)) {
    Write-Host "Error: Virtual environment (venv) not found at $projectPath" -ForegroundColor Red
    Write-Host "Script stopped. Please verify your paths." -ForegroundColor Yellow
    exit
}

# 3. Define the dictionary: Folder path = Key, Channel ID = Value
$uploads = [ordered]@{
    "C:\Users\My Computer\Downloads\Goethe Collection" = "-1004366014439"
    "C:\Users\My Computer\Downloads\The Fyodor Dostoevsky BBC Radio Drama Collection" = "-1004366014439"
    "C:\Users\My Computer\Downloads\The Leo Tolstoy BBC Radio Drama Collection Full-Cast Dramatisations of War and Peace, Anna Karenina & More" = "-1004366014439"    
    "C:\Users\My Computer\Downloads\Franz Kafka - Franz Kafka The Trial, Metamorphosis, Amerika & more A BBC Radio 4 full-cast drama collection" = "-1004366014439"
    "C:\Users\My Computer\Downloads\James Joyce, Radclyffe Hall, Aldous Huxley, George Orwell - Banned Books A BBC Radio Drama Collection" = "-1004366014439"
    "C:\Users\My Computer\Downloads\Bob Proctor - Principles Of Prosperity" = "-1003974841040"
    "C:\Users\My Computer\Downloads\Sophocles Greek Tragedies Collection" = "-1004494765351"
    "C:\Users\My Computer\Downloads\The Golden Ass or Metamorphoses - Apuleius (MP3)" = "-1004494765351"
    "C:\Users\My Computer\Downloads\Bigger Leaner Stronger - The Simple Science of Building the Ultimate Male Body (Unabridged Audiobook)" = "-1003974841040"
    "C:\Users\My Computer\Downloads\Design of Everyday Things Revised Edition by Donald A Norman" = "-1003974841040"
    "C:\Users\My Computer\Downloads\Epictetus - The Enchiridion & Discourses [Hayward B. Morse]" = "-1003974841040"
    "C:\Users\My Computer\Downloads\Susan Sanders, Tom Dotz, NLP Comprehensive, Tom Hoobyar - NLP The Essential Guide to Neuro-Linguistic Programming" = "-1003974841040"
    "C:\Users\My Computer\Downloads\Richard Bandler, Owen Fitzpatrick, Alessio Roberti - How to Take Charge of Your Life The User's Guide to NLP (Unabridged)" = "-1003974841040"
}

# 4. Loop through the folders
foreach ($folder in $uploads.Keys) {
    $channelId = $uploads[$folder]
    
    Write-Host "------------------------------------------------" -ForegroundColor Cyan
    Write-Host "Starting upload for $folder to channel $channelId..." -ForegroundColor Cyan
    
    # Use the call operator (&) to run the venv Python with your arguments
    & $venvPython .\main.py $folder $channelId
    
    # Error handling: If Python stops or crashes, halt the loop completely
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error or intentional stop during $folder upload. Script will not proceed to the next folder." -ForegroundColor Red
        break
    }
}

Write-Host "Process completed!" -ForegroundColor Green
Read-Host "Press Enter to exit..."