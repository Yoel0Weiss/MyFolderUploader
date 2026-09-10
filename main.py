import argparse
import os
import sys
import time
import asyncio
import mimetypes
from dotenv import load_dotenv
from telethon import TelegramClient, errors
from telethon.tl.types import DocumentAttributeAudio, DocumentAttributeVideo
from natsort import natsorted

# 1. Load secrets from .env file
load_dotenv()
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
TARGET_CHAT_ID = None

mimetypes.init()

# 2. Initialize Telegram Client
client = TelegramClient('uploader_session', API_ID, API_HASH)

HISTORY_FILE_NAME = 'uploaded_history.txt'

# Global variables for ETA calculation
total_bytes_to_upload = 0
uploaded_bytes_before_current_file = 0
upload_start_time = 0

def get_history_file_path(base_path):
    return os.path.join(base_path, HISTORY_FILE_NAME)

def load_history(base_path):
    history_path = get_history_file_path(base_path)
    if os.path.exists(history_path):
        with open(history_path, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_to_history(base_path, relative_file_path):
    history_path = get_history_file_path(base_path)
    with open(history_path, 'a', encoding='utf-8') as f:
        f.write(f"{relative_file_path}\n")

def format_time(seconds):
    if seconds < 0:
        return "00:00"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

def generate_tree(dir_path):
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
            if f != HISTORY_FILE_NAME:
                tree_str += f"{sub_indent}📄 {f}\n"
    return tree_str

async def send_long_message(chat_id, text, max_length=4000):
    """Splits a long text into multiple messages at newline boundaries and sends them"""
    lines = text.split('\n')
    current_message = ""
    
    for line in lines:
        # Check if adding the next line would exceed the Telegram limit
        if len(current_message) + len(line) + 1 > max_length:
            # Send the current accumulated chunk
            await client.send_message(chat_id, current_message)
            # Reset chunk and start with the current line
            current_message = line + '\n'
            # Sleep slightly to prevent Telegram spam limits on text messages
            await asyncio.sleep(1)
        else:
            current_message += line + '\n'
            
    # Send any remaining text
    if current_message.strip():
        await client.send_message(chat_id, current_message)

last_progress_display_time = 0

async def progress_callback(current, total):
    global uploaded_bytes_before_current_file
    global total_bytes_to_upload, upload_start_time
    global last_progress_display_time

    now = time.monotonic()

    # Update the terminal at most once every 5 seconds.
    if now - last_progress_display_time < 5 and current < total:
        return

    last_progress_display_time = now

    total_uploaded_now = uploaded_bytes_before_current_file + current
    elapsed_time = time.time() - upload_start_time

    if elapsed_time > 0 and total_uploaded_now > 0:
        speed = total_uploaded_now / elapsed_time
        remaining_bytes = total_bytes_to_upload - total_uploaded_now
        eta_seconds = remaining_bytes / speed
        eta_str = format_time(eta_seconds)
    else:
        eta_str = "Calculating..."

    percentage = (
        total_uploaded_now / total_bytes_to_upload * 100
        if total_bytes_to_upload > 0
        else 0
    )

    print(
        f"\rUploading... {percentage:.1f}% | ETA: {eta_str}   ",
        end="",
        flush=True,
    )

async def process_directory(base_path):
    global total_bytes_to_upload, uploaded_bytes_before_current_file, upload_start_time
    global last_progress_display_time

    last_progress_display_time = 0
    uploaded_history = load_history(base_path)
    is_resume = len(uploaded_history) > 0
    
    total_bytes_to_upload = 0
    files_to_upload_exist = False
    
    for root, dirs, files in os.walk(base_path):
         for f in files:
             if f == HISTORY_FILE_NAME:
                 continue
                 
             file_path = os.path.join(root, f)
             rel_path = os.path.relpath(file_path, base_path)
             
             if rel_path not in uploaded_history:
                 total_bytes_to_upload += os.path.getsize(file_path)
                 files_to_upload_exist = True
                 
    if not files_to_upload_exist:
        print("All files in this directory have already been uploaded!")
        return True
             
    uploaded_bytes_before_current_file = 0
    
    if not is_resume:
        print("Generating and sending directory tree to Telegram...")
        tree_text = generate_tree(base_path)
        # Use our new function to safely split and send the tree
        await send_long_message(TARGET_CHAT_ID, tree_text)
    else:
        print(f"Resuming upload. Found {len(uploaded_history)} files already uploaded.")
    
    upload_start_time = time.time() 

    for root, dirs, files in os.walk(base_path):
        if not files:
            continue
        
        relative_path = os.path.relpath(root, base_path)
        
        remaining_files_in_dir = [
            f for f in files 
            if f != HISTORY_FILE_NAME and os.path.relpath(os.path.join(root, f), base_path) not in uploaded_history
        ]
        
        if remaining_files_in_dir and relative_path != ".":
            path_display = f"{os.path.basename(base_path)} > " + relative_path.replace(os.sep, ' > ')
            await client.send_message(TARGET_CHAT_ID, f"📂 `{path_display}`")
        
        sorted_files = natsorted(files)
        
        for file_name in sorted_files:
            if file_name == HISTORY_FILE_NAME:
                continue
                
            file_path = os.path.join(root, file_name)
            rel_file_path = os.path.relpath(file_path, base_path)
            
            if rel_file_path in uploaded_history:
                continue
                
            file_size = os.path.getsize(file_path)
            
            if file_size == 0:
                print(f"Skipping empty file: {rel_file_path}")
                continue
            
            print(f"\nStarting upload for: {file_name}")
            
            mime_type, _ = mimetypes.guess_type(file_path)
            if file_name.lower().endswith(('.m4a', '.m4b')):
                mime_type = 'audio/mp4'
            elif mime_type is None:
                mime_type = ''

            audio_extensions = (
                '.mp3', '.m4a', '.m4b', '.m4p', '.wav', '.flac', '.ogg', '.oga',
                '.opus', '.aac', '.wma', '.amr', '.aiff', '.alac', '.ape', '.au',
                '.wv', '.rm', '.ra', '.spx', '.mid', '.midi'
            )

            video_extensions = (
                '.mp4', '.m4v', '.mkv', '.mov', '.avi', '.wmv', '.flv', '.webm'
            )

            is_audio = mime_type.startswith('audio/') or file_name.lower().endswith(audio_extensions)

            is_video = mime_type.startswith('video/') or file_name.lower().endswith(video_extensions)

            while True:
                try:
                    if is_audio:
                        attributes = [DocumentAttributeAudio(duration=0, title=os.path.splitext(file_name)[0], performer="")]
                        await client.send_file(
                            TARGET_CHAT_ID,
                            file_path,
                            caption=file_name,
                            mime_type=mime_type,
                            attributes=attributes,
                            force_document=False,
                            progress_callback=progress_callback
                        )
                    
                    elif is_video:
                        attributes = [DocumentAttributeVideo(duration=0, w=0, h=0, supports_streaming=True)]
                        await client.send_file(
                            TARGET_CHAT_ID,
                            file_path,
                            caption=file_name,
                            attributes=attributes,
                            force_document=False,
                            progress_callback=progress_callback
                        )
                    else:
                        await client.send_file(
                            TARGET_CHAT_ID,
                            file_path,
                            caption=file_name,
                            progress_callback=progress_callback
                        )

                    save_to_history(base_path, rel_file_path)
                    uploaded_bytes_before_current_file += file_size
                    await asyncio.sleep(2)
                    break

                except errors.FloodWaitError as e:
                    print(f"\n⏳ Telegram rate limit hit! Sleeping for {e.seconds} seconds to avoid ban...")
                    await asyncio.sleep(e.seconds)

                except Exception as e:
                    print(f"\n❌ An error occurred while uploading {file_name}: {e}")
                    print("Stopping the script safely. You can restart to resume.")
                    return False

    return True

async def main():
    global TARGET_CHAT_ID

    parser = argparse.ArgumentParser(description="Upload a directory to a Telegram chat.")
    parser.add_argument("directory", help="Path to the directory to upload")
    parser.add_argument("target_chat_id", type=int, help="Telegram destination chat or group ID")
    args = parser.parse_args()

    folder_to_upload = os.path.abspath(args.directory.strip(' "\''))
    TARGET_CHAT_ID = args.target_chat_id

    if not os.path.isdir(folder_to_upload):
        print(f"Error: The path '{folder_to_upload}' is invalid or is not a directory.")
        return 1

    print("Connecting to your Telegram account...")
    await client.start()
    print("Successfully connected! Starting process...")
    
    completed = await process_directory(folder_to_upload)
    if completed:
        print("\n✅ Upload completed successfully. All files have been processed.")
        return 0

    print("\n❌ Upload incomplete. Some files were not uploaded. Restart to resume.")
    return 1

if __name__ == '__main__':
    sys.exit(client.loop.run_until_complete(main()))