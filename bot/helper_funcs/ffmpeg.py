import asyncio
import os
import time
import re
import json
import subprocess
import math
import logging
import shutil
import shlex
from contextlib import asynccontextmanager
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.helper_funcs.display_progress import TimeFormatter, humanbytes
from bot.helper_funcs.utils import safe_float_convert, safe_int_convert, hbs, style_text
from bot.helper_funcs.database import db
from bot.config import AUTH_CHATS, AUTH_USERS
from bot.localisation import Localisation
from bot import (
    FINISHED_PROGRESS_STR,
    UN_FINISHED_PROGRESS_STR,
    DOWNLOAD_LOCATION,
    crf,
    resolution,
    audio_b,
    preset,
    codec,
    pid_list
)

LOGGER = logging.getLogger(__name__)

# Constants
FFMPEG_TIMEOUT = 10800  # 3 hours
PROGRESS_UPDATE_INTERVAL = 5
MAX_RETRIES = 3

# --- Utility Functions ---

def get_file_size(filepath):
    try:
        return os.path.getsize(filepath) if os.path.exists(filepath) else 0
    except Exception as e:
        LOGGER.error(f"Error getting file size: {e}")
        return 0

def cleanup_temp_files(file_paths):
    for filepath in file_paths:
        try:
            if filepath and os.path.exists(filepath):
                os.remove(filepath)
                LOGGER.info(f"Cleaned up: {filepath}")
        except Exception as e:
            LOGGER.warning(f"Could not clean up {filepath}: {e}")

def validate_video_file(filepath):
    """Check if the file has at least one video stream."""
    try:
        cmd = ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=codec_name', '-of', 'csv=p=0', filepath]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        return result.returncode == 0 and bool(result.stdout.strip())
    except Exception:
        return False

def escape_ffmpeg_path(path):
    """Escape path for FFmpeg filters."""
    # FFmpeg's filter path escaping is complex.
    # Colons and backslashes need to be escaped with a backslash.
    # Single quotes need to be escaped with a backslash and then another backslash for the shell if needed,
    # but here we're passing a list to subprocess so we just need FFmpeg's internal escaping.
    return path.replace('\\', '/').replace(':', '\\:').replace("'", "\\'")

# --- Metadata Functions ---

async def media_info(filepath):
    """Get media information using ffprobe in JSON format."""
    if not os.path.exists(filepath):
        LOGGER.error(f"File not found: {filepath}")
        return {}

    cmd = [
        'ffprobe', '-v', 'quiet', '-print_format', 'json',
        '-show_format', '-show_streams', '-show_chapters', filepath
    ]

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30)
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            LOGGER.error(f"ffprobe timed out for {filepath}")
            return {}

        if process.returncode != 0:
            LOGGER.error(f"ffprobe error: {stderr.decode()}")
            return {}

        return json.loads(stdout.decode())
    except Exception as e:
        LOGGER.error(f"Error getting media info: {e}")
        return {}

def get_duration(filepath):
    """Get duration of media file in seconds."""
    try:
        # Try ffprobe first as it's more reliable
        cmd = ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration', '-of', 'csv=p=0', filepath]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode == 0 and result.stdout.strip():
            return safe_float_convert(result.stdout.strip())

        # Fallback to hachoir
        parser = createParser(filepath)
        if parser:
            metadata = extractMetadata(parser)
            if metadata and metadata.has('duration'):
                return safe_float_convert(metadata.get('duration').total_seconds())
    except Exception as e:
        LOGGER.error(f"Error getting duration: {e}")
    return 0

def get_codec(filepath):
    """Get video codec of the file."""
    try:
        cmd = ['ffprobe', '-v', 'quiet', '-select_streams', 'v:0', '-show_entries', 'stream=codec_name', '-of', 'csv=p=0', filepath]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception as e:
        LOGGER.error(f"Error getting codec: {e}")
    return "Unknown"

# --- FFmpeg Execution with Progress ---

async def run_ffmpeg_with_progress(cmd, total_duration, bot, message, description="Processing..."):
    """Run FFmpeg command and update progress on Telegram."""
    progress_file = os.path.join(DOWNLOAD_LOCATION, f"progress_{int(time.time() * 1000)}_{message.id}.txt")

    if '-progress' not in cmd:
        cmd.insert(1, '-progress')
        cmd.insert(2, progress_file)

    with open(progress_file, 'w') as f: f.write("")

    start_time = time.time()
    process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    pid_list.insert(0, process.pid)
    LOGGER.info(f"FFmpeg started (PID: {process.pid})")

    progress_msg = None
    try:
        progress_msg = await bot.send_message(chat_id=message.chat.id, text=f"🚀 {description}", reply_to_message_id=message.id)
    except Exception: pass

    async def progress_monitor():
        last_update_time = 0
        while process.returncode is None:
            await asyncio.sleep(PROGRESS_UPDATE_INTERVAL)
            if not os.path.exists(progress_file): continue

            try:
                with open(progress_file, 'rb') as f:
                    try: f.seek(-512, os.SEEK_END)
                    except OSError: pass
                    content = f.read().decode('utf-8', errors='ignore')
            except Exception: continue

            if not content: continue
            data = {}
            for line in content.split('\n'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    data[key.strip()] = value.strip()

            if data.get('progress') == 'end': break

            speed = safe_float_convert(data.get('speed', '0x').replace('x', ''))
            if speed <= 0: speed = 0.001

            out_time_us = safe_int_convert(data.get('out_time_us', 0))
            elapsed_seconds = out_time_us / 1000000.0
            percentage = min(max((elapsed_seconds / total_duration) * 100 if total_duration > 0 else 0, 0), 99.9)

            eta_seconds = (total_duration - elapsed_seconds) / speed
            eta = TimeFormatter(eta_seconds * 1000) if eta_seconds > 0 else "Calculating..."

            bar = FINISHED_PROGRESS_STR * int(percentage / 10) + UN_FINISHED_PROGRESS_STR * (10 - int(percentage / 10))
            execution_time = TimeFormatter((time.time() - start_time) * 1000)

            stats_text = (
                f"<b>{style_text(description)}</b>\n\n"
                f"<blockquote>"
                f"<b>{style_text('Progress:')}</b> [{bar}] {percentage:.2f}%\n"
                f"<b>{style_text('Speed:')}</b> {speed:.2f}x | <b>{style_text('FPS:')}</b> {data.get('fps', 0)}\n"
                f"<b>{style_text('Bitrate:')}</b> {data.get('bitrate', '0kbits/s')}\n"
                f"<b>{style_text('Elapsed:')}</b> {execution_time}\n"
                f"<b>{style_text('ETA:')}</b> {eta}"
                f"</blockquote>"
            )

            if time.time() - last_update_time >= 10 and progress_msg:
                try:
                    await progress_msg.edit_text(text=stats_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_{process.pid}")]]))
                    last_update_time = time.time()
                except Exception: pass

    monitor_task = asyncio.create_task(progress_monitor())
    success = False

    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=FFMPEG_TIMEOUT)
        success = process.returncode == 0
        if not success:
            LOGGER.error(f"FFmpeg failed (PID: {process.pid}, Code: {process.returncode})\nSTDERR: {stderr.decode().strip()}")
    except asyncio.TimeoutError:
        LOGGER.error(f"FFmpeg timed out (PID: {process.pid})")
        process.kill()
    except Exception as e:
        LOGGER.error(f"FFmpeg error (PID: {process.pid}): {e}")
    finally:
        monitor_task.cancel()
        if process.pid in pid_list: pid_list.remove(process.pid)
        if os.path.exists(progress_file): os.remove(progress_file)
        if progress_msg:
            try: await progress_msg.delete()
            except Exception: pass

    return success

# --- Core Processing Functions ---

async def get_encoding_settings(settings=None, res_key=None):
    """Get consistent encoding settings from global database or provided settings."""
    if not res_key and settings:
        res_key = settings.get('resolution', "480p")

    if not res_key:
        res_key = "480p"

    # Normalize res_key to keys used in DB (480p, 720p, 1080p)
    res_key = str(res_key).lower().replace('p', '')
    if res_key in ["480", "640", "854"]:
        res_key = "480p"
    elif res_key in ["720", "1280"]:
        res_key = "720p"
    elif res_key in ["1080", "1920"]:
        res_key = "1080p"
    else:
        res_key = "480p"

    from bot.helper_funcs.database import get_global_settings
    g = await get_global_settings(res_key)

    v_codec = g.get('codec', 'libx264')
    v_crf = g.get('crf', '30')
    v_bitrate = g.get('video_bitrate')
    if v_bitrate in ["Auto/None", "None", None]:
        v_bitrate = None

    v_preset = g.get('preset', 'superfast')
    v_res = str(g.get('resolution', '640x360')).lower().replace('p', '')
    a_bitrate = g.get('audio_b', '48k')

    # Normalize dimensions from resolution string like "640x360"
    if 'x' in v_res:
        res_w, res_h = v_res.split('x')
    elif ':' in v_res:
        res_w, res_h = v_res.split(':')
    else:
        res_w, res_h = "-2", v_res

    return {
        'codec': v_codec,
        'crf': str(v_crf),
        'video_bitrate': v_bitrate,
        'preset': v_preset,
        'res_w': res_w,
        'res_h': res_h,
        'audio_bitrate': a_bitrate,
        'audio_codec': g.get('audio_codec', 'libopus'),
        'bits': g.get('bits', '8 bits'),
        'watermark': g.get('watermark', 'None'),
        'wm_size': g.get('wm_size', '0')
    }

async def convert_video(video_file, output_directory, total_time, bot, message, settings=None):
    """Main compression function."""
    if not os.path.exists(video_file):
        return None

    total_duration = safe_float_convert(total_time)
    if total_duration == 0:
        total_duration = get_duration(video_file)

    os.makedirs(output_directory, exist_ok=True)

    base_name = os.path.splitext(os.path.basename(video_file))[0]
    s = await get_encoding_settings(settings)

    # Determine extension based on codec
    ext = ".mp4" if s['codec'] in ['libx264', 'libx265'] else ".mkv"
    output_file = os.path.join(output_directory, f"[Encoded] {base_name}{ext}")

    has_video = validate_video_file(video_file)
    LOGGER.info(f"File: {video_file}, has_video: {has_video}, settings: {s}")

    cmd = [
        'ffmpeg', '-hide_banner', '-loglevel', 'warning',
        '-i', video_file,
        '-map', '0',
    ]

    if has_video:
        cmd.extend(['-c:v', s['codec']])
        if s.get('video_bitrate'):
            cmd.extend(['-b:v', str(s['video_bitrate'])])
        else:
            cmd.extend(['-crf', s['crf']])

        cmd.extend(['-preset', s['preset']])
        if s['codec'] == 'libx264':
            cmd.extend(['-x264-params', 'bframes=8:psy-rd=1:ref=3:aq-mode=3:aq-strength=0.8:deblock=1,1'])
        elif s['codec'] == 'libx265':
            cmd.extend(['-x265-params', 'bframes=8:psy-rd=1:ref=3:aq-mode=3:aq-strength=0.8:deblock=1,1'])

        cmd.extend([
            '-vf', f"scale={s['res_w']}:{s['res_h']}:force_original_aspect_ratio=decrease,format=yuv420p",
            '-level', '3.1',
        ])
    else:
        LOGGER.warning(f"No video stream detected or ffprobe failed for {video_file}. Attempting to copy video stream.")
        cmd.extend(['-c:v', 'copy'])

    cmd.extend([
        '-c:a', s.get('audio_codec', 'libopus'), '-b:a', s['audio_bitrate'],
        '-ac', '2', '-ab', s['audio_bitrate'], '-vbr', '2',
        '-c:s', 'copy', '-threads', '5', '-y', output_file
    ])

    LOGGER.info(f"Starting FFmpeg with command: {' '.join(cmd)}")
    success = await run_ffmpeg_with_progress(cmd, total_duration, bot, message, "Compressing Video...")

    if not success:
        LOGGER.error("FFmpeg process returned success=False")
    elif not os.path.exists(output_file):
        LOGGER.error(f"FFmpeg succeeded but output file does not exist: {output_file}")
    elif os.path.getsize(output_file) <= 1000:
        LOGGER.error(f"FFmpeg succeeded but output file is too small ({os.path.getsize(output_file)} bytes): {output_file}")

    return output_file if success and os.path.exists(output_file) and os.path.getsize(output_file) > 1000 else None

async def convert_video_custom(video_file, output_directory, total_time, bot, message, ffmpegcode):
    """Run video compression with custom FFmpeg flags string."""
    if not os.path.exists(video_file):
        return None

    total_duration = safe_float_convert(total_time)
    if total_duration == 0:
        total_duration = get_duration(video_file)

    os.makedirs(output_directory, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(video_file))[0]

    # Simple heuristic to determine extension from the ffmpegcode
    # Defaults to .mp4 if libx264/265 are mentioned, otherwise .mkv
    ext = ".mkv"
    if "libx264" in ffmpegcode or "libx265" in ffmpegcode:
        ext = ".mp4"

    output_file = os.path.join(output_directory, f"[Encoded] {base_name}{ext}")

    # Build the full command
    # Expected ffmpegcode is just the flags (e.g., "-c:v libx264 ...")
    flags = shlex.split(ffmpegcode)

    cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'warning', '-i', video_file]
    cmd.extend(flags)
    cmd.extend(['-y', output_file])

    LOGGER.info(f"Starting custom FFmpeg with command: {' '.join(cmd)}")
    success = await run_ffmpeg_with_progress(cmd, total_duration, bot, message, "Custom Compression...")

    return output_file if success and os.path.exists(output_file) and os.path.getsize(output_file) > 1000 else None

async def convert_video_all(video_file, output_directory, total_time, bot, message, settings=None):
    """Encode 480p, 720p, and 1080p simultaneously."""
    if not os.path.exists(video_file): return []

    total_duration = safe_float_convert(total_time) or get_duration(video_file)
    os.makedirs(output_directory, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(video_file))[0]

    s480 = await get_encoding_settings(res_key="480p")
    s720 = await get_encoding_settings(res_key="720p")
    s1080 = await get_encoding_settings(res_key="1080p")

    settings_map = {"480p": s480, "720p": s720, "1080p": s1080}
    ext_map = {res: (".mp4" if s['codec'] in ['libx264', 'libx265'] else ".mkv") for res, s in settings_map.items()}
    outputs = {res: os.path.join(output_directory, f"[{res}] {base_name}{ext_map[res]}") for res in settings_map}

    filter_complex = "split=3[v1][v2][v3]; " + "; ".join([f"[v{i+1}]scale={settings_map[res]['res_w']}:{settings_map[res]['res_h']}:force_original_aspect_ratio=decrease,format=yuv420p[out{res}]" for i, res in enumerate(settings_map)])

    cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'warning', '-i', video_file, '-filter_complex', filter_complex]

    for res, s in settings_map.items():
        cmd.extend(['-map', f'[out{res}]', '-map', '0:a?', '-map', '0:s?', '-map', '0:d?'])
        cmd.extend(['-c:v', s['codec'], '-preset', s['preset']])
        if s.get('video_bitrate'): cmd.extend(['-b:v', str(s['video_bitrate'])])
        else: cmd.extend(['-crf', s['crf']])

        if s['codec'] in ['libx264', 'libx265']:
            cmd.extend([f'-{s["codec"].replace("lib", "")}-params', 'bframes=8:psy-rd=1:ref=3:aq-mode=3:aq-strength=0.8:deblock=1,1'])

        cmd.extend(['-level', '3.1', '-c:a', s.get('audio_codec', 'libopus'), '-b:a', s['audio_bitrate'], '-ac', '2', '-ab', s['audio_bitrate'], '-vbr', '2', '-c:s', 'copy', '-threads', '5', '-y', outputs[res]])

    success = await run_ffmpeg_with_progress(cmd, total_duration, bot, message, "Multi-Resolution Encoding...")
    return [p for p in outputs.values() if success and os.path.exists(p) and os.path.getsize(p) > 1000]

async def cut_video(video_file, output_directory, start_time, end_time, bot, message, settings=None):
    """Trim video with optional re-encoding using same settings."""
    if not os.path.exists(video_file):
        return None

    os.makedirs(output_directory, exist_ok=True)
    output_file = os.path.join(output_directory, f"trimmed_{int(time.time())}.mkv")

    start_s = safe_float_convert(start_time)
    end_s = safe_float_convert(end_time)
    duration = max(end_s - start_s, 0)

    if settings:
        s = await get_encoding_settings(settings)
        has_video = validate_video_file(video_file)

        cmd = [
            'ffmpeg', '-ss', str(start_s), '-i', video_file, '-t', str(duration),
            '-map', '0',
        ]

        if has_video:
            cmd.extend(['-c:v', s['codec'], '-crf', s['crf'], '-preset', s['preset']])
            if s['codec'] == 'libx264':
                cmd.extend(['-x264-params', 'bframes=8:psy-rd=1:ref=3:aq-mode=3:aq-strength=0.8:deblock=1,1'])
            elif s['codec'] == 'libx265':
                cmd.extend(['-x265-params', 'bframes=8:psy-rd=1:ref=3:aq-mode=3:aq-strength=0.8:deblock=1,1'])

            cmd.extend([
                '-vf', f"scale={s['res_w']}:{s['res_h']}:force_original_aspect_ratio=decrease,format=yuv420p",
                '-level', '3.1',
            ])
        else:
            cmd.extend(['-c:v', 'copy'])

        cmd.extend([
            '-c:a', 'libopus', '-b:a', s['audio_bitrate'],
            '-ac', '2', '-ab', s['audio_bitrate'], '-vbr', '2',
            '-c:s', 'copy', '-threads', '5', '-y', output_file
        ])

        success = await run_ffmpeg_with_progress(cmd, duration, bot, message, f"Trimming & Compressing...")
    else:
        # Fast trim without re-encoding
        cmd = [
            'ffmpeg', '-ss', str(start_s), '-i', video_file, '-t', str(duration),
            '-c', 'copy', '-map', '0', '-y', output_file
        ]
        process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        await process.communicate()
        success = process.returncode == 0

    return output_file if success and os.path.exists(output_file) else None

async def merge_videos(video_list, output_path, bot, message, total_duration):
    """Merge multiple videos/audios using concat demuxer."""
    if not video_list:
        return None
    
    # For videos, ensure output is .mkv for better compatibility with copied streams
    # For audios, keep the requested extension (usually .mp3)
    is_audio = output_path.lower().endswith(('.mp3', '.m4a', '.ogg', '.opus', '.wav'))
    if not is_audio and not output_path.endswith('.mkv'):
        output_path = os.path.splitext(output_path)[0] + '.mkv'

    list_file = os.path.join(DOWNLOAD_LOCATION, f"merge_list_{message.id}_{int(time.time())}.txt")
    with open(list_file, 'w') as f:
        for video in video_list:
            # Proper escaping for FFmpeg concat demuxer:
            # Single quotes must be escaped by doubling them OR using backslash.
            # Here we use backslash escaping for quotes and backslashes.
            abs_path = os.path.abspath(video).replace("\\", "\\\\").replace("'", "\\'")
            f.write(f"file '{abs_path}'\n")

    cmd = [
        'ffmpeg', '-f', 'concat', '-safe', '0', '-i', list_file,
        '-c', 'copy', '-y', output_path
    ]

    success = await run_ffmpeg_with_progress(cmd, total_duration, bot, message, "Merging Videos...")

    if os.path.exists(list_file): os.remove(list_file)
    return output_path if success and os.path.exists(output_path) else None

# --- Audio/Subtitle Manipulation ---

async def extract_audio(video_file, output_directory):
    if not os.path.exists(video_file): return None
    output_file = os.path.join(output_directory, f"audio_{int(time.time())}.mp3")
    cmd = ['ffmpeg', '-i', video_file, '-vn', '-acodec', 'libmp3lame', '-q:a', '2', '-y', output_file]
    process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        LOGGER.error(f"Extract audio failed: {stderr.decode()}")
    return output_file if os.path.exists(output_file) else None

async def extract_subtitles(video_file, output_directory):
    if not os.path.exists(video_file): return None
    # We'll try to extract the first subtitle stream
    output_file = os.path.join(output_directory, f"sub_{int(time.time())}.srt")
    cmd = ['ffmpeg', '-i', video_file, '-map', '0:s:0', '-c:s', 'srt', '-y', output_file]
    process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        LOGGER.error(f"Extract subtitles failed: {stderr.decode()}")
        # Fallback to .ass if srt fails or isn't compatible
        output_file = os.path.join(output_directory, f"sub_{int(time.time())}.ass")
        cmd = ['ffmpeg', '-i', video_file, '-map', '0:s:0', '-c:s', 'ass', '-y', output_file]
        process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        await process.communicate()

    return output_file if os.path.exists(output_file) and os.path.getsize(output_file) > 0 else None

async def add_audio(video_file, audio_file, output_directory):
    output_file = os.path.join(output_directory, f"muxed_{int(time.time())}.mkv")
    cmd = ['ffmpeg', '-i', video_file, '-i', audio_file, '-c:v', 'copy', '-c:a', 'aac', '-map', '0:v:0?', '-map', '1:a?', '-shortest', '-y', output_file]
    process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        LOGGER.error(f"Add audio failed: {stderr.decode()}")
    return output_file if os.path.exists(output_file) else None

async def remove_audio(video_file, output_directory):
    output_file = os.path.join(output_directory, f"no_audio_{int(time.time())}.mkv")
    cmd = ['ffmpeg', '-i', video_file, '-an', '-vcodec', 'copy', '-y', output_file]
    process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        LOGGER.error(f"Remove audio failed: {stderr.decode()}")
    return output_file if os.path.exists(output_file) else None

async def add_soft_subtitles(video_file, subtitle_file, output_directory):
    output_file = os.path.join(output_directory, f"soft_sub_{int(time.time())}.mkv")
    cmd = ['ffmpeg', '-i', video_file, '-i', subtitle_file, '-c', 'copy', '-map', '0', '-map', '1', '-y', output_file]
    process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        LOGGER.error(f"Add soft subtitles failed: {stderr.decode()}")
    return output_file if os.path.exists(output_file) else None

async def add_hard_subtitles(video_file, subtitle_file, output_directory, bot, message, settings=None):
    if not os.path.exists(video_file) or not os.path.exists(subtitle_file): return None

    total_duration = get_duration(video_file)
    output_file = os.path.join(output_directory, f"hard_sub_{int(time.time())}.mkv")
    s = await get_encoding_settings(settings)
    escaped_path = escape_ffmpeg_path(subtitle_file)

    cmd = [
        'ffmpeg', '-i', video_file,
        '-vf', f"scale={s['res_w']}:{s['res_h']}:force_original_aspect_ratio=decrease,subtitles='{escaped_path}':force_style='FontSize=16',format=yuv420p",
        '-c:v', s['codec'], '-preset', s['preset'],
    ]
    if s.get('video_bitrate'): cmd.extend(['-b:v', str(s['video_bitrate'])])
    else: cmd.extend(['-crf', s['crf']])

    if s['codec'] in ['libx264', 'libx265']:
        cmd.extend([f'-{s["codec"].replace("lib", "")}-params', 'bframes=8:psy-rd=1:ref=3:aq-mode=3:aq-strength=0.8:deblock=1,1'])

    cmd.extend([
        '-level', '3.1', '-c:a', 'libopus', '-b:a', s['audio_bitrate'],
        '-ac', '2', '-ab', s['audio_bitrate'], '-vbr', '2',
        '-map', '0', '-threads', '5', '-y', output_file
    ])

    success = await run_ffmpeg_with_progress(cmd, total_duration, bot, message, "Adding Hard Subtitles...")
    return output_file if success and os.path.exists(output_file) else None

async def remove_subtitles(video_file, output_directory):
    output_file = os.path.join(output_directory, f"no_sub_{int(time.time())}.mkv")
    cmd = ['ffmpeg', '-i', video_file, '-sn', '-c', 'copy', '-y', output_file]
    process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        LOGGER.error(f"Remove subtitles failed (code {process.returncode}): {stderr.decode()}")
    return output_file if os.path.exists(output_file) else None

# --- Thumbnail & Screenshot ---

def get_thumbnail(filepath, output_path, time_offset='00:00:01'):
    try:
        cmd = [
            'ffmpeg', '-ss', time_offset, '-i', filepath, '-vframes', '1',
            '-vf', 'scale=320:240:force_original_aspect_ratio=decrease,pad=320:240:(ow-iw)/2:(oh-ih)/2:color=black',
            '-y', output_path
        ]
        subprocess.run(cmd, capture_output=True, timeout=30)
        return output_path if os.path.exists(output_path) else None
    except Exception:
        return None

def take_screen_shot(video_file, output_directory, ttl):
    os.makedirs(output_directory, exist_ok=True)
    output_file = os.path.join(output_directory, f"ss_{int(time.time())}.jpg")
    try:
        cmd = ['ffmpeg', '-ss', str(ttl), '-i', video_file, '-vframes', '1', '-y', output_file]
        subprocess.run(cmd, capture_output=True, timeout=30)
        return output_file if os.path.exists(output_file) else None
    except Exception:
        return None

# --- Formatting & Media Info Text ---

async def get_media_info_text(filepath):
    """Generate a detailed MediaInfo-style report."""
    # Use mediainfo CLI if available
    mediainfo_path = shutil.which("mediainfo")
    if mediainfo_path:
        process = await asyncio.create_subprocess_exec(
            mediainfo_path, '--Full', filepath,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode == 0:
            return stdout.decode().strip()

    # Fallback to ffprobe
    data = await media_info(filepath)
    if not data: return "Failed to fetch media information."

    output = []

    # General
    fmt = data.get('format', {})
    output.append("General")
    output.append(f"Complete name                            : {os.path.basename(filepath)}")
    output.append(f"Format                                   : {fmt.get('format_name', 'Unknown').upper()}")
    output.append(f"File size                                : {hbs(safe_int_convert(fmt.get('size', 0)))}")
    output.append(f"Duration                                 : {TimeFormatter(safe_float_convert(fmt.get('duration')) * 1000)}")
    output.append(f"Overall bit rate                         : {int(safe_int_convert(fmt.get('bit_rate', 0)) / 1000)} kbps")
    output.append("")

    # Streams
    for stream in data.get('streams', []):
        stype = stream.get('codec_type', 'unknown').capitalize()
        output.append(f"{stype}")
        output.append(f"ID                                       : {stream.get('index')}")
        output.append(f"Format                                   : {stream.get('codec_name', 'Unknown').upper()}")
        output.append(f"Format/Info                              : {stream.get('codec_long_name', 'Unknown')}")

        if stype == "Video":
            output.append(f"Width                                    : {stream.get('width')} pixels")
            output.append(f"Height                                   : {stream.get('height')} pixels")
            output.append(f"Display aspect ratio                     : {stream.get('display_aspect_ratio', 'N/A')}")
            output.append(f"Frame rate                               : {stream.get('avg_frame_rate', 'N/A')} fps")
            output.append(f"Color space                              : {stream.get('color_space', 'N/A')}")
            output.append(f"Chroma subsampling                       : {stream.get('pix_fmt', 'N/A')}")
            output.append(f"Bit depth                                : {stream.get('bits_per_raw_sample', '8')} bits")
        elif stype == "Audio":
            output.append(f"Channel(s)                               : {stream.get('channels')} channels")
            output.append(f"Sampling rate                            : {stream.get('sample_rate')} Hz")
            output.append(f"Bit rate                                 : {int(safe_int_convert(stream.get('bit_rate', 0)) / 1000)} kbps")
            lang = stream.get('tags', {}).get('language')
            if lang: output.append(f"Language                                 : {lang}")
        elif stype == "Subtitle":
            lang = stream.get('tags', {}).get('language')
            if lang: output.append(f"Language                                 : {lang}")
            title = stream.get('tags', {}).get('title')
            if title: output.append(f"Title                                    : {title}")

        output.append("")

    return "\n".join(output).strip()

