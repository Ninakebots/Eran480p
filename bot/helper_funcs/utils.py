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

import os, asyncio, pyrogram, psutil, platform, time, re
from bot import data
from pyrogram.types import Message
from psutil import disk_usage, cpu_percent, virtual_memory, Process as psprocess


def checkKey(dict, key):
    if key in dict.keys():
        return True
    else:
        return False

def hbs(size):
    try:
        if not size or size == 0:
            return "0 B"
        
        if isinstance(size, str):
            try:
                size = float(re.sub(r'[^\d.]', '', size))
            except (ValueError, TypeError):
                return "0 B"
        
        size = float(size)
        if size < 0:
            return "0 B"
            
        power = 1024
        raised_to_pow = 0
        dict_power_n = {0: "B", 1: "KB", 2: "MB", 3: "GB", 4: "TB", 5: "PB"}
        
        while size >= power and raised_to_pow < 5:
            size = size / power
            raised_to_pow += 1
            
        return f"{round(size, 2)} {dict_power_n[raised_to_pow]}"
    except Exception as e:
        LOGGER.error(f"Error in hbs function: {e}")
        return "0 B"

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
        os.system('rm -rf /app/downloads/*')
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
        message = await e.reply_text(f"<u><b>Sʏꜱᴛᴇᴍ Sᴛᴀᴛꜱ 🧮</b></u>\n"
                                     f"<blockquote><b>🎖️ CPU Freq:</b> {freq_current}\n"
                                     f"<b>CPU Cores [ Physical:</b> {cpu_count} | <b>Total:</b> {cpu_count_logical} ]\n\n"
                                     f"<b>💾 Total Disk :</b> {psutil._common.bytes2human(disk.total)}B\n"
                                     f"<b>Used:</b> {psutil._common.bytes2human(disk.used)}B | <b>Free:</b> {psutil._common.bytes2human(disk.free)}B\n\n"
                                     f"<b>🔺 Total Upload:</b> {psutil._common.bytes2human(ul_size)}B\n"
                                     f"<b>🔻 Total Download:</b> {psutil._common.bytes2human(dl_size)}B\n\n"
                                     f"<b>🎮 Total Ram :</b> {psutil._common.bytes2human(ram_stats.total)}B\n"
                                     f"<b>Used:</b>{psutil._common.bytes2human(ram_stats.used)}B | <b>Free:</b> {psutil._common.bytes2human(ram_stats.available)}B\n\n"
                                     f"<b>🖥 CPU:</b> {cpuUsage}%\n"
                                     f"<b>🎮 RAM:</b> {int(ram_stats.percent)}%\n"
                                     f"<b>💿 DISK:</b> {int(disk.percent)}%</blockquote>")
    except Exception as e:
        LOGGER.error(f"Error in sysinfo: {e}")
        await e.reply_text("Error getting system information")

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
