# Telegram Bulk Directory Uploader

A robust, automated Python script designed to upload large, multi-level directories (10GB+) to a Telegram channel or group. It maintains the folder hierarchy, sorts files naturally, and includes a persistent resume mechanism to handle network drops or rate limits overnight.

## ✨ Features

* **State Persistence (Resume Mechanism):** Creates an `uploaded_history.txt` file inside the target directory. If the script is stopped, crashes, or you pause it to sleep, it resumes exactly where it left off without re-uploading existing files.
* **Dynamic Audio Handling:** Uses MIME-type detection to ensure audio files (MP3, M4A, WAV, etc.) are uploaded as playable Telegram audio messages rather than raw documents.
* **Anti-Spam Protection:** Automatically catches Telegram's `FloodWaitError`, goes to sleep for the exact required duration, and retries the upload without crashing.
* **Smart Directory Tree & Navigation:** Generates and sends a visual directory tree before uploading. Safely splits the tree into multiple messages if it exceeds Telegram's 4,096-character limit. Sends breadcrumb messages (`📂 Folder > Subfolder`) during traversal.
* **Natural Sorting:** Files are uploaded in true alphabetical/numerical order (e.g., 1, 2, 10 instead of 1, 10, 2).
* **Live ETA & Progress:** Displays a real-time console progress bar and Estimated Time of Arrival (ETA) based on the total bytes left to upload.

## 📋 Prerequisites

* Python 3.7 or higher.
* A Telegram API ID and API Hash (obtainable from [my.telegram.org](https://my.telegram.org)).

## 🚀 Installation

1. **Clone the repository:**
   ```bash
   git clone <your_repo_url>
   cd <your_project_directory>
   ```

2. **Create and activate a Virtual Environment:**
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Mac/Linux:
   source venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install telethon natsort python-dotenv
   ```

4. **Environment Setup:**
   Create a `.env` file in the root directory of the project and add your Telegram credentials:
   ```
   API_ID=your_api_id_here
   API_HASH=your_api_hash_here
   ```
   The destination chat ID is supplied as a command-line argument.

## 🛠️ Usage

1. **Run the script with two arguments:**
   ```bash
   python main.py "C:\Path\To\Folder" -100123456789
   ```
   The first argument is the directory to upload. The second argument is the Telegram destination chat or group ID.

2. **PowerShell pipeline example:**
   ```powershell
   $folders = @("C:\Folder1", "C:\Folder2")
   foreach ($folder in $folders) {
       python .\main.py $folder -100123456789
       if ($LASTEXITCODE -ne 0) { break }
   }
   ```
   The next upload starts only when the previous command exits with code `0`. An incomplete upload exits with code `1` and can be resumed safely.

3. **First Run Only:** You will be prompted to enter your phone number and the Telegram login code to generate the `uploader_session.session` file.

⚠️ Important Notes
File Size Limit: Telegram limits uploads for standard users to 2GB per file (4GB for Premium users). Ensure no single file in your directory exceeds this limit.

Restarting Uploads: If you want to re-upload the same directory from scratch (e.g., to a different channel), simply delete the uploaded_history.txt file located inside that specific target directory.