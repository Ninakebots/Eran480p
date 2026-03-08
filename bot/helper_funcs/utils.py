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
    """Concurrent task worker to replace sequential recursive add_task."""
    LOGGER.info("Starting Task Worker...")
    while True:
        task_info = await TASK_QUEUE.get()
        task_id = task_info.get('id')
        try:
            # Check if task is still in data list (not cancelled)
            if not any(d.get('id') == task_id for d in data):
                LOGGER.info(f"Task {task_id} was cancelled, skipping...")
                continue

            # Mark as processing
            for d in data:
                if d.get('id') == task_id:
                    d['status'] = 'processing'
                    break

            from bot.helper_funcs.task_handler import execute_task
            await execute_task(task_info)
        except Exception as e:
            import traceback
            LOGGER.error(f"Error in task_worker: {e}\n{traceback.format_exc()}")
        finally:
            # Mark current task as done in the 'data' list for status monitoring
            for i, d in enumerate(data):
                if d.get('id') == task_id:
                    data.pop(i)
                    break
            TASK_QUEUE.task_done()

# Start the worker task when the module is imported
# This requires an existing event loop, usually handled in __main__.py
# but we can provide a startup function.
def start_task_worker():
    for _ in range(3):
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
            if task.get('status') == 'processing':
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
    from bot.helper_funcs.output import copy_to_dump_channel as copy_to_dump
    await copy_to_dump(bot, message, user_id)

async def output_handler(bot, update, output_path, download_time=None, encoding_time=None, thumb_path=None, input_path=None, sent_message=None):
    from bot.helper_funcs.output import output_handler as out_handler
    await out_handler(bot, update, output_path, download_time, encoding_time, thumb_path, input_path, sent_message)

async def upload_to_telegraph(title, content):
    from bot.helper_funcs.output import upload_to_telegraph as telegraph_upload
    return await telegraph_upload(title, content)

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
