import asyncio
import os
import time
import re
import json
import subprocess
import math
import logging
import shutil
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

    # Ensure -progress is in the command
    if '-progress' not in cmd:
        # Insert after 'ffmpeg'
        cmd.insert(1, '-progress')
        cmd.insert(2, progress_file)

    # Initialize progress file
    with open(progress_file, 'w') as f: f.write("")

    start_time = time.time()
    process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    LOGGER.info(f"FFmpeg started (PID: {process.pid}): {' '.join(cmd)}")
    pid_list.insert(0, process.pid)

    progress_msg = None
    try:
        progress_msg = await bot.send_message(chat_id=message.chat.id, text=f"🚀 {description}", reply_to_message_id=message.id)
    except Exception:
        pass

    last_update_time = 0
    success = False

    try:
        while process.returncode is None:
            await asyncio.sleep(PROGRESS_UPDATE_INTERVAL)

            if time.time() - start_time > FFMPEG_TIMEOUT:
                LOGGER.error("FFmpeg process timed out")
                process.terminate()
                break

            if not os.path.exists(progress_file):
                continue

            # Read progress data
            try:
                # Read from the end of file to get latest stats
                with open(progress_file, 'rb') as f:
                    try:
                        f.seek(-512, os.SEEK_END)
                    except OSError:
                        pass
                    content = f.read().decode('utf-8', errors='ignore')
            except Exception:
                continue

            if not content: continue

            # Parse progress
            data = {}
            for line in content.split('\n'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    data[key.strip()] = value.strip()

            if data.get('progress') == 'end':
                success = True
                break

            # Calculate stats
            frame = safe_int_convert(data.get('frame', 0))
            fps = safe_float_convert(data.get('fps', 0))
            bitrate = data.get('bitrate', '0kbits/s')
            speed_str = data.get('speed', '0x').replace('x', '')
            speed = safe_float_convert(speed_str)
            if speed <= 0: speed = 0.001 # Avoid division by zero

            out_time_us = safe_int_convert(data.get('out_time_us', 0))
            elapsed_seconds = out_time_us / 1000000.0

            percentage = (elapsed_seconds / total_duration) * 100 if total_duration > 0 else 0
            percentage = min(max(percentage, 0), 99.9)

            eta_seconds = (total_duration - elapsed_seconds) / speed
            eta = TimeFormatter(eta_seconds * 1000) if eta_seconds > 0 else "Calculating..."

            # Build progress string
            filled = int(percentage / 10)
            bar = FINISHED_PROGRESS_STR * filled + UN_FINISHED_PROGRESS_STR * (10 - filled)

            execution_time = TimeFormatter((time.time() - start_time) * 1000)

            stats_text = (
                f"<b>{style_text(description)}</b>\n\n"
                f"<blockquote>"
                f"<b>{style_text('Progress:')}</b> [{bar}] {percentage:.2f}%\n"
                f"<b>{style_text('Speed:')}</b> {speed:.2f}x | <b>{style_text('FPS:')}</b> {fps}\n"
                f"<b>{style_text('Bitrate:')}</b> {bitrate}\n"
                f"<b>{style_text('Elapsed:')}</b> {execution_time}\n"
                f"<b>{style_text('ETA:')}</b> {eta}"
                f"</blockquote>"
            )

            if time.time() - last_update_time >= 10 and progress_msg:
                try:
                    await progress_msg.edit_text(
                        text=stats_text,
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_{process.pid}")
                        ]])
                    )
                    last_update_time = time.time()
                except Exception:
                    pass

        stdout, stderr = await process.communicate()
        if process.returncode == 0:
            success = True
            LOGGER.info(f"FFmpeg process completed successfully (PID: {process.pid})")
        else:
            stderr_out = stderr.decode().strip() if stderr else "No error output"
            stdout_out = stdout.decode().strip() if stdout else "No standard output"

            LOGGER.error(f"FFmpeg failed (PID: {process.pid}, Code: {process.returncode})")
            LOGGER.error(f"STDOUT: {stdout_out}")
            LOGGER.error(f"STDERR: {stderr_out}")
            # Log the command that failed for easier debugging
            LOGGER.debug(f"Failed command: {' '.join(cmd)}")
            success = False

    except Exception as e:
        LOGGER.error(f"Error in FFmpeg progress loop: {e}")
    finally:
        if process.returncode is None:
            process.kill()
            await process.wait()

        if process.pid in pid_list:
            pid_list.remove(process.pid)

        if os.path.exists(progress_file):
            os.remove(progress_file)

        if progress_msg:
            try:
                await progress_msg.delete()
            except Exception:
                pass

    return success

# --- Core Processing Functions ---

def get_encoding_settings(settings=None):
    """Get consistent encoding settings from provided settings or globals."""
    if settings:
        v_codec = settings.get('codec', codec[0] if codec else "libsvtav1")
        v_crf = settings.get('crf', crf[0] if crf else "24")
        v_preset = settings.get('preset', preset[0] if preset else "veryfast")
        v_res = settings.get('resolution', resolution[0] if resolution else "1280x720")
        a_bitrate = settings.get('audio_b', audio_b[0] if audio_b else "128k")
    else:
        v_codec = codec[0] if codec else "libsvtav1"
        v_crf = crf[0] if crf else "24"
        v_preset = preset[0] if preset else "veryfast"
        v_res = resolution[0] if resolution else "1280x720"
        a_bitrate = audio_b[0] if audio_b else "128k"

    # Normalize resolution
    v_res = str(v_res).replace('p', '')
    if 'x' in v_res:
        res_w, res_h = v_res.split('x')
    elif ':' in v_res:
        res_w, res_h = v_res.split(':')
    else:
        # User specified just a height, like "480"
        if v_res == "480":
            res_w, res_h = "854", "480"
        elif v_res == "720":
            res_w, res_h = "1280", "720"
        elif v_res == "1080":
            res_w, res_h = "1920", "1080"
        else:
            res_w, res_h = "-2", v_res

    return {
        'codec': v_codec,
        'crf': str(v_crf),
        'preset': v_preset,
        'res_w': res_w,
        'res_h': res_h,
        'audio_bitrate': a_bitrate
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
    s = get_encoding_settings(settings)

    # Determine extension based on codec
    ext = ".mp4" if s['codec'] in ['libx264', 'libx265'] else ".mkv"
    output_file = os.path.join(output_directory, f"[Encoded] {base_name}{ext}")

    has_video = validate_video_file(video_file)
    LOGGER.info(f"File: {video_file}, has_video: {has_video}, settings: {s}")

    cmd = [
        'ffmpeg', '-hide_banner', '-loglevel', 'warning',
        '-i', video_file,
        '-map', '0:v:0?', '-map', '0:a?', '-map', '0:s?',
    ]

    if has_video:
        cmd.extend([
            '-c:v', s['codec'], '-crf', s['crf'], '-preset', s['preset'],
            '-vf', f"scale={s['res_w']}:{s['res_h']}:force_original_aspect_ratio=decrease,format=yuv420p",
        ])
    else:
        LOGGER.warning(f"No video stream detected or ffprobe failed for {video_file}. Attempting to copy video stream.")
        cmd.extend(['-c:v', 'copy'])

    cmd.extend([
        '-c:a', 'aac', '-b:a', s['audio_bitrate'],
        '-c:s', 'copy', '-y', output_file
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
        s = get_encoding_settings(settings)
        has_video = validate_video_file(video_file)

        cmd = [
            'ffmpeg', '-ss', str(start_s), '-i', video_file, '-t', str(duration),
            '-map', '0:v:0?', '-map', '0:a?', '-map', '0:s?',
        ]

        if has_video:
            cmd.extend([
                '-c:v', s['codec'], '-crf', s['crf'], '-preset', s['preset'],
                '-vf', f"scale={s['res_w']}:{s['res_h']}:force_original_aspect_ratio=decrease,format=yuv420p",
            ])
        else:
            cmd.extend(['-c:v', 'copy'])

        cmd.extend([
            '-c:a', 'aac', '-b:a', s['audio_bitrate'],
            '-c:s', 'copy', '-y', output_file
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

    s = get_encoding_settings(settings)

    # Advanced escaping for subtitles filter
    # FFmpeg subtitles filter requires escaping for colons and single quotes
    # The path itself should be escaped for the filter argument
    escaped_path = subtitle_file.replace('\\', '/').replace(':', '\\:').replace("'", r"\'")

    cmd = [
        'ffmpeg', '-i', video_file,
        '-vf', f"scale={s['res_w']}:{s['res_h']}:force_original_aspect_ratio=decrease,subtitles='{escaped_path}':force_style='FontSize=16',format=yuv420p",
        '-c:v', s['codec'], '-crf', s['crf'], '-preset', s['preset'],
        '-c:a', 'aac', '-b:a', s['audio_bitrate'],
        '-map', '0:v:0?', '-map', '0:a?', '-y', output_file
    ]

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

