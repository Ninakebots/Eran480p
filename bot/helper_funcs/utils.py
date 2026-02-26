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
    if not size:
        return "0 B"
    for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
        if size < 1024.0:
            break
        size /= 1024.0
    return f"{size:.2f} {unit}"

async def on_task_complete():
    try:
        if len(data) > 0:
            del data[0]
        if len(data) > 0:
            await add_task(data[0])
    except Exception as e:
        LOGGER.error(f"Error in on_task_complete: {e}")

async def add_task(task_info):
    try:
        # Safer cleanup of downloads directory
        from bot import DOWNLOAD_LOCATION
        os.makedirs(DOWNLOAD_LOCATION, exist_ok=True)
        if os.path.exists(DOWNLOAD_LOCATION):
            for file in os.listdir(DOWNLOAD_LOCATION):
                file_path = os.path.join(DOWNLOAD_LOCATION, file)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    LOGGER.warning(f"Failed to delete {file_path}: {e}")

        # We'll import the actual handler here to avoid circular imports
        from bot.helper_funcs.task_handler import execute_task
        await execute_task(task_info)
    except Exception as e:
        import traceback
        LOGGER.error(f"Error in add_task: {e}")
        LOGGER.error(f"Full traceback: {traceback.format_exc()}")
    finally:
        await on_task_complete()

async def add_to_queue(message: Message, task_type: str, options: dict = None):
    task_info = {
        'message': message,
        'task_type': task_type,
        'options': options or {},
        'id': int(time.time())
    }
    data.append(task_info)
    if len(data) == 1:
        # If this is the only task, start it
        await add_task(task_info)
    return task_info['id']

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
            f"<u><b>Sʏꜱᴛᴇᴍ Sᴛᴀᴛꜱ 🧮</b></u>\n"
            f"<blockquote>"
            f"<b>🎖️ CPU Freq:</b> `{freq_current}`\n"
            f"<b>CPU Cores:</b> `{cpu_count}` physical | `{cpu_count_logical}` logical\n\n"
            f"<b>💾 Disk:</b> `{hbs(disk.used)}` / `{hbs(disk.total)}` ({disk.percent}%)\n"
            f"<b>🎮 RAM:</b> `{hbs(ram_stats.used)}` / `{hbs(ram_stats.total)}` ({ram_stats.percent}%)\n\n"
            f"<b>🔺 Uploaded:</b> `{hbs(ul_size)}` | <b>🔻 Downloaded:</b> `{hbs(dl_size)}`"
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

async def copy_to_dump_channel(bot, message, user_id):
    from bot import DUMP_CHANNEL
    if not DUMP_CHANNEL:
        return
    try:
        # Handle conversion of DUMP_CHANNEL to int if it's a numeric string
        dump_chat = int(DUMP_CHANNEL) if str(DUMP_CHANNEL).strip("-").isdigit() else DUMP_CHANNEL
        caption = f"**User ID:** `{user_id}`\n\n{message.caption or ''}"

        if message.video:
            await bot.send_video(chat_id=dump_chat, video=message.video.file_id, caption=caption)
        elif message.audio:
            await bot.send_audio(chat_id=dump_chat, audio=message.audio.file_id, caption=caption)
        elif message.document:
            await bot.send_document(chat_id=dump_chat, document=message.document.file_id, caption=caption)
    except Exception as e:
        LOGGER.error(f"Error copying to dump channel: {e}")

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
