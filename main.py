import os
import time
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient
from natsort import natsorted

# 1. Load secrets from .env file
load_dotenv()
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
TARGET_CHAT_ID = os.getenv('TARGET_CHAT_ID')

try:
    TARGET_CHAT_ID = int(TARGET_CHAT_ID)
except (ValueError, TypeError):
    pass

# 2. Initialize Telegram Client
client = TelegramClient('uploader_session', API_ID, API_HASH)

# Global variables for ETA calculation across multiple files
total_bytes_to_upload = 0
uploaded_bytes_before_current_file = 0
upload_start_time = 0

def format_time(seconds):
    """Converts seconds into a readable MM:SS format"""
    if seconds < 0:
        return "00:00"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

def generate_tree(dir_path):
    """Generates a text-based representation of the directory tree"""
    tree_str = f"🌳 Directory Tree for: {os.path.basename(dir_path)}\n\n"
    for root, dirs, files in os.walk(dir_path):
        
        if root == dir_path:
            level = 0
        else:
            level = len(os.path.relpath(root, dir_path).split(os.sep))
            
        indent = ' ' * 4 * level
        tree_str += f"{indent}📂 {os.path.basename(root)}/\n"
        
        sub_indent = ' ' * 4 * (level + 1)
        for f in natsorted(files):
            tree_str += f"{sub_indent}📄 {f}\n"
    return tree_str

async def progress_callback(current, total):
    """Prints upload progress percentage and ETA to the console"""
    global uploaded_bytes_before_current_file, total_bytes_to_upload, upload_start_time
    
    total_uploaded_now = uploaded_bytes_before_current_file + current
    
    elapsed_time = time.time() - upload_start_time
    
    if elapsed_time > 0 and total_uploaded_now > 0:
        # Calculate speed (bytes per second)
        speed = total_uploaded_now / elapsed_time
        # Calculate remaining bytes
        remaining_bytes = total_bytes_to_upload - total_uploaded_now
        # Calculate ETA
        eta_seconds = remaining_bytes / speed
        eta_str = format_time(eta_seconds)
    else:
         eta_str = "Calculating..."
         
    # We clear the line and print the new info
    percentage = (total_uploaded_now / total_bytes_to_upload) * 100 if total_bytes_to_upload > 0 else 0
    print(f"\rUploading... {percentage:.1f}% | ETA: {eta_str}   ", end='', flush=True)


async def process_directory(base_path):
    """Main logic: mapping, directory traversal (DFS), and uploading"""
    global total_bytes_to_upload, uploaded_bytes_before_current_file, upload_start_time
    
    # 1. First Pass: Calculate total bytes to upload
    total_bytes_to_upload = 0
    for root, dirs, files in os.walk(base_path):
         for f in files:
             file_path = os.path.join(root, f)
             total_bytes_to_upload += os.path.getsize(file_path)
             
    uploaded_bytes_before_current_file = 0
    
    print("Generating and sending directory tree to Telegram...")
    tree_text = generate_tree(base_path)
    
    if len(tree_text) > 4000:
        tree_text = tree_text[:4000] + "\n... (Tree is too long and was truncated)"
    
    await client.send_message(TARGET_CHAT_ID, tree_text)
    
    upload_start_time = time.time() # Start the timer right before the first upload

    for root, dirs, files in os.walk(base_path):
        if not files:
            continue
        
        relative_path = os.path.relpath(root, base_path)
        
        if relative_path != ".":
            path_display = f"{os.path.basename(base_path)} > " + relative_path.replace(os.sep, ' > ')
            await client.send_message(TARGET_CHAT_ID, f"📂 `{path_display}`")
        
        sorted_files = natsorted(files)
        
        for file_name in sorted_files:
            file_path = os.path.join(root, file_name)
            file_size = os.path.getsize(file_path)
            
            print(f"\nStarting upload for: {file_name}")
            
            await client.send_file(
                TARGET_CHAT_ID,
                file_path,
                caption=file_name,
                progress_callback=progress_callback
            )
            
            # After a successful upload, add its size to the global counter
            uploaded_bytes_before_current_file += file_size
            await asyncio.sleep(2)

async def main():
    raw_input = input("Enter the full path to the directory you want to upload: ")
    folder_to_upload = os.path.abspath(raw_input.strip(' "\''))
    
    if not os.path.isdir(folder_to_upload):
        print(f"Error: The path '{folder_to_upload}' is invalid or is not a directory.")
        return

    print("Connecting to your Telegram account...")
    await client.start()
    print("Successfully connected! Starting process...")
    
    await process_directory(folder_to_upload)
    
    print("\n✅ Done! All files have been uploaded in order.")

if __name__ == '__main__':
    client.loop.run_until_complete(main())