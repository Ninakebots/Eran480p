# Developer: @TheAlphaBotz
# Organization: Anime Junctions
# © 2025 All Rights Reserved
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)
LOGGER = logging.getLogger(__name__)

import os, asyncio, pyrogram, psutil, platform, time, re, json, aiohttp, shutil
from bot import data, AUTH_USERS, AUTH_CHATS
from bot.helper_funcs.database import db
from pyrogram import filters
from pyrogram.types import Message
from psutil import disk_usage, cpu_percent, virtual_memory, Process as psprocess


def checkKey(dict, key):
    if key in dict.keys():
        return True
    else:
        return False

def hbs(size):
    if not size: return "0 B"
    for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
        if size < 1024.0: break
        size /= 1024.0
    return f"{size:.2f} {unit}"

# Global task queue
TASK_QUEUE = asyncio.Queue()

async def task_worker():
    """Sequential task worker to replace recursive add_task."""
    LOGGER.info("Starting Task Worker...")
    while True:
        task_info = await TASK_QUEUE.get()
        try:
            # Safer cleanup of downloads directory
            from bot import DOWNLOAD_LOCATION
            os.makedirs(DOWNLOAD_LOCATION, exist_ok=True)
            for file in os.listdir(DOWNLOAD_LOCATION):
                file_path = os.path.join(DOWNLOAD_LOCATION, file)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path): os.unlink(file_path)
                    elif os.path.isdir(file_path): shutil.rmtree(file_path)
                except Exception as e: LOGGER.warning(f"Failed to delete {file_path}: {e}")

            from bot.helper_funcs.task_handler import execute_task
            await execute_task(task_info)
        except Exception as e:
            import traceback
            LOGGER.error(f"Error in task_worker: {e}\n{traceback.format_exc()}")
        finally:
            # Mark current task as done in the 'data' list for status monitoring
            if data and data[0]['id'] == task_info['id']:
                data.pop(0)
            TASK_QUEUE.task_done()

# Start the worker task when the module is imported
# This requires an existing event loop, usually handled in __main__.py
# but we can provide a startup function.
def start_task_worker():
    asyncio.create_task(task_worker())

async def add_to_queue(message: Message, task_type: str, options: dict = None):
    task_info = {
        'message': message,
        'task_type': task_type,
        'options': options or {},
        'id': time.time_ns()
    }
    data.append(task_info)
    await TASK_QUEUE.put(task_info)
    return task_info['id']

async def remove_from_queue(message_id: int):
    """Remove a pending task from the queue."""
    for i, task in enumerate(data):
        if task.get('message') and task.get('message').id == message_id:
            if i == 0:
                # Active task, don't remove (it's already processing)
                return False
            data.pop(i)
            return True
    return False

async def sysinfo(e):
    try:
        cpuUsage = psutil.cpu_percent(interval=0.5)
        cpu_freq = psutil.cpu_freq()
        freq_current = f"{round(cpu_freq.current / 1000, 2)} GHz" if cpu_freq else "Unknown"
        cpu_count = psutil.cpu_count(logical=False)
        cpu_count_logical = psutil.cpu_count(logical=True)
        ram_stats = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        dl_size = psutil.net_io_counters().bytes_recv
        ul_size = psutil.net_io_counters().bytes_sent

        text = (
            f"<u><b>{style_text('System Stats')} 🧮</b></u>\n"
            f"<blockquote>"
            f"<b>🎖️ {style_text('CPU Freq:')}</b> `{freq_current}`\n"
            f"<b>{style_text('CPU Cores:')}</b> `{cpu_count}` {style_text('physical')} | `{cpu_count_logical}` {style_text('logical')}\n\n"
            f"<b>💾 {style_text('Disk:')}</b> `{hbs(disk.used)}` / `{hbs(disk.total)}` ({disk.percent}%)\n"
            f"<b>🎮 {style_text('RAM:')}</b> `{hbs(ram_stats.used)}` / `{hbs(ram_stats.total)}` ({ram_stats.percent}%)\n\n"
            f"<b>🔺 {style_text('Uploaded:')}</b> `{hbs(ul_size)}` | <b>🔻 {style_text('Downloaded:')}</b> `{hbs(dl_size)}`"
            f"</blockquote>"
        )
        await e.reply_text(text)
    except Exception as e:
        LOGGER.error(f"Error in sysinfo: {e}")
        await e.reply_text(f"❌ Error getting system information: `{e}`")

def safe_float_convert(value, default=0.0):
    try:
        if isinstance(value, (int, float)):
            return float(value)
        elif isinstance(value, str):
            cleaned = re.sub(r'[^\d.]', '', value)
            return float(cleaned) if cleaned else default
        return default
    except (ValueError, TypeError):
        return default

def style_text(text):
    """
    Converts alphanumeric characters to Mathematical Sans-Serif font (𝖠𝖻𝖼𝖽).
    Ignores HTML tags, curly-brace placeholders, and URLs.
    """
    if not text or not isinstance(text, str):
        return text

    # Character mapping for Mathematical Sans-Serif
    # A-Z: U+1D5A0 - U+1D5B9 (𝖠-𝖹)
    # a-z: U+1D5BA - U+1D5D3 (𝖺-𝗓)
    # 0-9: U+1D7E2 - U+1D7EB (𝟢-𝟫)

    def transform(char):
        if 'A' <= char <= 'Z':
            return chr(ord(char) - ord('A') + 0x1D5A0)
        elif 'a' <= char <= 'z':
            return chr(ord(char) - ord('a') + 0x1D5BA)
        elif '0' <= char <= '9':
            return chr(ord(char) - ord('0') + 0x1D7E2)
        return char

    # Protect HTML tags, curly-brace placeholders, URLs, and bot commands
    # Bot commands: starts with / followed by alphanumeric chars and potentially @botusername
    # We use a non-capturing group (?:...) for @botusername to keep things simple with re.split
    pattern = r'(<[^>]+>|\{[^}]*\}|https?://[^\s<>"]+|/[a-zA-Z0-9_]+(?:@[a-zA-Z0-9_]+)?)'
    parts = re.split(pattern, text)

    for i in range(len(parts)):
        # Even indices are the text to be styled
        # Captured groups (protected parts) are at odd indices
        if i % 2 == 0 and parts[i]:
            parts[i] = ''.join(transform(c) for c in parts[i])

    return ''.join(p for p in parts if p is not None)

async def copy_to_dump_channel(bot, message, user_id):
    from bot import DUMP_CHANNEL
    if not DUMP_CHANNEL:
        return
    try:
        # Handle conversion of DUMP_CHANNEL to int if it's a numeric string
        # Pyrogram requires channel IDs to be integers starting with -100
        dump_chat = DUMP_CHANNEL
        if isinstance(dump_chat, str):
            if dump_chat.startswith("-100") or dump_chat.isdigit() or (dump_chat.startswith("-") and dump_chat[1:].isdigit()):
                try:
                    dump_chat = int(dump_chat)
                except ValueError:
                    pass

        caption = f"**User ID:** `{user_id}`\n\n{message.caption or ''}"

        # Using copy is more robust as it handles all media types and metadata
        await message.copy(
            chat_id=dump_chat,
            caption=caption
        )
    except Exception as e:
        LOGGER.error(f"Error copying to dump channel: {e}")

async def output_handler(bot, update, output_path, download_time=None, encoding_time=None, thumb_path=None, input_path=None, sent_message=None):
    from bot.localisation import Localisation
    from bot.helper_funcs.display_progress import progress_for_pyrogram, TimeFormatter
    from bot.helper_funcs.database import get_user_data
    from bot.helper_funcs.gofile import upload_gofile
    from bot import GOFILE_TOKEN
    import time

    user_id = update.from_user.id if update.from_user else update.chat.id
    user_settings = await get_user_data(user_id)
    upload_dest = user_settings.get("upload_destination", "chat")
    upload_as = user_settings.get("upload_as", "video")

    # Determine destination chat
    dest_chat = update.chat.id
    if upload_dest == "pm":
        dest_chat = user_id
    elif isinstance(upload_dest, int):
        dest_chat = upload_dest

    u_start = time.time()
    if not sent_message:
        sent_message = await bot.send_message(chat_id=update.chat.id, text=Localisation.UPLOAD_START, reply_to_message_id=update.id)
    else:
        try:
            await sent_message.edit_text(text=Localisation.UPLOAD_START)
        except:
            pass

    try:
        # Generate initial caption
        d_time = download_time or "N/A"
        e_time = encoding_time or "N/A"

        # We use .replace to match existing style and support both indexed and non-indexed placeholders
        # Step 5 will ensure COMPRESS_SUCCESS has 3 sets of {}
        caption = Localisation.COMPRESS_SUCCESS.replace('{}', d_time, 1).replace('{}', e_time, 1)

        # Upload
        upload = None
        if upload_dest == "gofile":
            try:
                await sent_message.edit_text("📤 **Uploading to Gofile.io...**")
                download_url = await upload_gofile(output_path, token=GOFILE_TOKEN)
                if download_url:
                    u_time = TimeFormatter((time.time() - u_start) * 1000)
                    file_name = os.path.basename(output_path)
                    file_size = hbs(os.path.getsize(output_path))

                    text = (
                        f"✅ **" + style_text("File Encoded & Uploaded to Gofile!") + "**\n\n"
                        f"📁 **" + style_text("File Name:") + "** `{file_name}`\n"
                        f"⚖️ **" + style_text("Size:") + "** `{file_size}`\n"
                        f"🔗 **" + style_text("Download Link:") + "** {download_url}\n\n"
                        f"<blockquote>"
                        f"<b>📥 " + style_text("Download Time:") + "</b> {d_time}\n"
                        f"<b>📀 " + style_text("Encoding Time:") + "</b> {e_time}\n"
                        f"<b>📤 " + style_text("Upload Time:") + "</b> {u_time}"
                        f"</blockquote>"
                    )
                    await bot.send_message(
                        chat_id=update.chat.id,
                        text=text,
                        reply_to_message_id=update.id,
                        disable_web_page_preview=True
                    )
                else:
                    raise Exception("Gofile upload failed.")
            except Exception as e:
                LOGGER.error(f"Gofile upload error: {e}")
                upload_dest = "telegram" # Fallback to telegram
                await sent_message.edit_text("⚠️ Gofile upload failed. Falling back to Telegram...")

        if upload_dest != "gofile":
            ext = output_path.split('.')[-1].lower()
            common_args = {
                'chat_id': dest_chat,
                'caption': caption.replace('{}', "Calculating...", 1),
                'reply_to_message_id': update.id if dest_chat == update.chat.id else None,
                'progress': progress_for_pyrogram,
                'progress_args': (bot, Localisation.UPLOAD_START, sent_message, u_start)
            }

            if upload_as == "video" and ext in ['mp4', 'mkv', 'webm']:
                upload = await bot.send_video(
                    video=output_path,
                    thumb=thumb_path if thumb_path and os.path.exists(thumb_path) else None,
                    supports_streaming=True,
                    **common_args
                )
            elif ext in ['mp3', 'm4a', 'ogg', 'opus']:
                upload = await bot.send_audio(
                    audio=output_path,
                    thumb=thumb_path if thumb_path and os.path.exists(thumb_path) else None,
                    **common_args
                )
            else:
                upload = await bot.send_document(
                    document=output_path,
                    thumb=thumb_path if thumb_path and os.path.exists(thumb_path) else None,
                    force_document=True,
                    **common_args
                )

            u_time = TimeFormatter((time.time() - u_start) * 1000)

            if upload:
                # Update caption with actual upload time
                try:
                    final_caption = caption.replace('{}', u_time, 1)
                    await upload.edit_caption(caption=final_caption)
                except Exception as e:
                    LOGGER.error(f"Error editing caption: {e}")

                # Copy to dump channel
                await copy_to_dump_channel(bot, upload, update.from_user.id if update.from_user else "Unknown")

        try:
            if sent_message:
                await sent_message.delete()
        except:
            pass

    except Exception as e:
        LOGGER.error(f"Upload error: {e}")
        try:
            await sent_message.edit_text(f"❌ Upload failed: {str(e)[:100]}")
        except:
            pass
    finally:
        # Centralized cleanup
        user_id = update.from_user.id if update.from_user else "default"
        custom_thumb = os.path.join("thumbnails", f"{user_id}.jpg")

        for p in [output_path, thumb_path, input_path]:
            if p and os.path.exists(p):
                # Don't delete the custom thumbnail
                if os.path.abspath(p) == os.path.abspath(custom_thumb):
                    continue
                try:
                    if os.path.isfile(p): os.remove(p)
                    elif os.path.isdir(p): shutil.rmtree(p)
                except Exception as e:
                    LOGGER.warning(f"Failed to cleanup {p}: {e}")

TELEGRAPH_TOKEN = None

async def upload_to_telegraph(title, content):
    global TELEGRAPH_TOKEN
    try:
        async with aiohttp.ClientSession() as session:
            if not TELEGRAPH_TOKEN:
                # Create account anonymously
                async with session.get("https://api.telegra.ph/createAccount", params={
                    "short_name": "EncoderBot",
                    "author_name": "ZaniEncoder"
                }) as resp:
                    acc_data = await resp.json()
                    if not acc_data.get("ok"):
                        return None
                    TELEGRAPH_TOKEN = acc_data["result"]["access_token"]

            # Content must be a list of nodes. We'll wrap our text in <pre>
            formatted_content = [{"tag": "pre", "children": [content]}]

            async with session.post("https://api.telegra.ph/createPage", data={
                "access_token": TELEGRAPH_TOKEN,
                "title": title,
                "author_name": "ZaniEncoder",
                "content": json.dumps(formatted_content),
                "return_content": "false"
            }) as resp:
                page_data = await resp.json()
                if page_data.get("ok"):
                    return page_data["result"]["url"]
                else:
                    LOGGER.error(f"Telegraph error: {page_data}")
                    # If token is invalid, clear it so it's recreated next time
                    if "ACCESS_TOKEN_INVALID" in str(page_data):
                        TELEGRAPH_TOKEN = None
                    return None
    except Exception as e:
        LOGGER.error(f"Error uploading to Telegraph: {e}")
        return None

async def auth_filter(_, __, update):
    user_id = update.from_user.id if update.from_user else None
    if hasattr(update, "chat") and update.chat:
        chat_id = update.chat.id
    elif hasattr(update, "message") and update.message and update.message.chat:
        chat_id = update.message.chat.id
    else:
        chat_id = None

    # Check hardcoded admins
    if user_id in AUTH_USERS or chat_id in AUTH_USERS:
        return True

    # Check hardcoded chats
    if chat_id in AUTH_CHATS:
        return True

    # Check database
    if await db.is_chat_authorized(chat_id):
        return True

    if user_id and await db.is_chat_authorized(user_id):
        return True

    return False

is_auth = filters.create(auth_filter)

def personal_auth_filter(_, __, update):
    user_id = update.from_user.id if update.from_user else None
    return user_id in AUTH_USERS and user_id > 0

is_personal_auth = filters.create(personal_auth_filter)

def safe_int_convert(value, default=0):
    try:
        if isinstance(value, int):
            return value
        elif isinstance(value, float):
            return int(value)
        elif isinstance(value, str):
            cleaned = re.sub(r'[^\d]', '', value)
            return int(cleaned) if cleaned else default
        return default
    except (ValueError, TypeError):
        return default
