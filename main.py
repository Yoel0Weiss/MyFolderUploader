import os
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient
from natsort import natsorted

# 1. Load secrets from .env file
load_dotenv()
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
TARGET_CHAT_ID = os.getenv('TARGET_CHAT_ID')

# Telegram requires numerical chat IDs to be integers
try:
    TARGET_CHAT_ID = int(TARGET_CHAT_ID)
except (ValueError, TypeError):
    pass # Keep as string if it's a username (e.g., @mychannel)

# 2. Initialize Telegram Client
client = TelegramClient('uploader_session', API_ID, API_HASH)

def generate_tree(dir_path):
    """Generates a text-based representation of the directory tree"""
    tree_str = f"🌳 Directory Tree for: {os.path.basename(dir_path)}\n\n"
    for root, dirs, files in os.walk(dir_path):
        # Calculate depth to format the indentation
        level = root.replace(dir_path, '').count(os.sep)
        indent = ' ' * 4 * level
        
        tree_str += f"{indent}📂 {os.path.basename(root)}/\n"
        
        sub_indent = ' ' * 4 * (level + 1)
        for f in natsorted(files):
            tree_str += f"{sub_indent}📄 {f}\n"
    return tree_str

async def progress_callback(current, total):
    """Prints the upload progress percentage to the console"""
    print(f"Uploading... {current * 100 / total:.1f}%", end='\r')

async def process_directory(base_path):
    """Main logic: mapping, directory traversal (DFS), and uploading"""
    
    print("Generating and sending directory tree to Telegram...")
    tree_text = generate_tree(base_path)
    
    # Telegram limits messages to 4096 characters. Truncate if necessary
    if len(tree_text) > 4000:
        tree_text = tree_text[:4000] + "\n... (Tree is too long and was truncated)"
    
    await client.send_message(TARGET_CHAT_ID, tree_text)

    # os.walk traverses top-down (similar to DFS)
    for root, dirs, files in os.walk(base_path):
        if not files:
            continue # Skip directories with no files
        
        # Build the relative path for breadcrumbs navigation
        relative_path = os.path.relpath(root, base_path)
        if relative_path == ".":
            path_display = os.path.basename(base_path)
        else:
            path_display = f"{os.path.basename(base_path)} > " + relative_path.replace(os.sep, ' > ')
        
        # Send current directory notification
        await client.send_message(TARGET_CHAT_ID, f"📂 Current Directory:\n`{path_display}`")
        
        # Natural sort for files
        sorted_files = natsorted(files)
        
        for file_name in sorted_files:
            file_path = os.path.join(root, file_name)
            print(f"\nStarting upload for: {file_name}")
            
            # Upload the file to Telegram
            await client.send_file(
                TARGET_CHAT_ID,
                file_path,
                caption=file_name,
                progress_callback=progress_callback
            )
            
            # Short 2-second delay between files to avoid FloodWait limits
            await asyncio.sleep(2)

async def main():
    folder_to_upload = input("Enter the full path to the directory you want to upload: ")
    
    if not os.path.isdir(folder_to_upload):
        print("Error: The path is invalid or is not a directory.")
        return

    print("Connecting to your Telegram account...")
    await client.start()
    print("Successfully connected! Starting process...")
    
    await process_directory(folder_to_upload)
    
    print("\n✅ Done! All files have been uploaded in order.")

if __name__ == '__main__':
    client.loop.run_until_complete(main())