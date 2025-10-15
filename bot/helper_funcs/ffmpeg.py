import asyncio
import os
import time
import re
import json
import subprocess
import math
import logging
from contextlib import asynccontextmanager
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.helper_funcs.display_progress import TimeFormatter
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
FFMPEGTIMEOUT = 7200
PROGRESSUPDATEINTERVAL = 8
MAXRETRIES = 3


def safe_float_convert(value, default=0.0):
    try:
        if isinstance(value, (int, float)):
            return float(value)
        elif isinstance(value, str):
            cleaned = re.sub(r'[^0-9.]', '', value)
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
            cleaned = re.sub(r'[^0-9]', '', value)
            return int(cleaned) if cleaned else default
        return default
    except (ValueError, TypeError):
        return default

async def media_info(saved_file_path):
    try:
        if not os.path.exists(saved_file_path):
            LOGGER.error(f"File not found: {saved_file_path}")
            return {}
        process = await asyncio.create_subprocess_exec(
            'ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams',
            saved_file_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30)
        except asyncio.TimeoutError:
            LOGGER.error("ffprobe timeout")
            process.kill()
            return {}
        if process.returncode != 0:
            LOGGER.error(f"ffprobe error: {stderr.decode()}")
            return {}
        return json.loads(stdout.decode())
    except Exception as e:
        LOGGER.error(f"Error getting media info: {e}")
        return {}

def get_codec(filepath):
    try:
        if not os.path.exists(filepath):
            return "Unknown"
        metadata = extractMetadata(createParser(filepath))
        if metadata and hasattr(metadata, 'exportPlaintext'):
            for line in metadata.exportPlaintext():
                if 'Video codec' in line and ':' in line:
                    return line.split(':')[1].strip()
        return "Unknown"
    except Exception as e:
        LOGGER.error(f"Error getting codec: {e}")
        return "Unknown"

def get_duration(filepath):
    try:
        if not os.path.exists(filepath):
            LOGGER.error(f"File not found for duration: {filepath}")
            return 0
        metadata = extractMetadata(createParser(filepath))
        if metadata and hasattr(metadata, 'get'):
            duration = metadata.get('duration')
            if duration:
                return safe_float_convert(duration.total_seconds())
        try:
            cmd = ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration', '-of', 'csv=p=0', filepath]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0 and result.stdout.strip():
                return safe_float_convert(result.stdout.strip())
        except Exception as probe_error:
            LOGGER.error(f"ffprobe duration error: {probe_error}")
        return 0
    except Exception as e:
        LOGGER.error(f"Error getting duration: {e}")
        return 0

def get_thumbnail(filepath, output_path, time_offset='00:00:01'):
    try:
        if not os.path.exists(filepath):
            LOGGER.error(f"Source file not found: {filepath}")
            return None
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        cmd = ['ffmpeg', '-i', filepath, '-ss', time_offset, '-vframes', '1',
               '-vf', 'scale=320:240:force_original_aspect_ratio=decrease,pad=320:240:(ow-iw)/2:(oh-ih)/2:color=black',
               '-y', output_path]
        result = subprocess.run(cmd, capture_output=True, timeout=60)
        if result.returncode == 0 and os.path.exists(output_path):
            return output_path
        else:
            LOGGER.error(f"Thumbnail generation failed: {result.stderr.decode()}")
            return None
    except subprocess.TimeoutExpired:
        LOGGER.error("Thumbnail generation timeout")
        return None
    except Exception as e:
        LOGGER.error(f"Error generating thumbnail: {e}")
        return None

def take_screen_shot(video_file, output_directory, ttl):
    try:
        if not os.path.exists(video_file):
            return None
        os.makedirs(output_directory, exist_ok=True)
        output_filename = f"{output_directory}/screenshot{int(time.time())}.jpg"
        ttl_safe = safe_float_convert(ttl)
        cmd = ['ffmpeg', '-ss', str(ttl_safe), '-i', video_file, '-vframes', '1', '-y', output_filename]
        result = subprocess.run(cmd, capture_output=True, timeout=60)
        if result.returncode == 0 and os.path.exists(output_filename):
            return output_filename
        return None
    except subprocess.TimeoutExpired:
        LOGGER.error("Screenshot timeout")
        return None
    except Exception as e:
        LOGGER.error(f"Error taking screenshot: {e}")
        return None

async def cult_small_video(video_file, output_directory, start_time, end_time, bot, message):
    try:
        if not os.path.exists(video_file):
            return None
        os.makedirs(output_directory, exist_ok=True)
        output_filename = f"{output_directory}/trimmed{int(time.time())}.mp4"
        start_safe = safe_float_convert(start_time)
        end_safe = safe_float_convert(end_time)
        cmd = ['ffmpeg', '-i', video_file, '-ss', str(start_safe), '-to', str(end_safe), '-c', 'copy', '-y', output_filename]
        process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)
        except asyncio.TimeoutError:
            process.kill()
            LOGGER.error("Video cutting timeout")
            return None
        if process.returncode == 0 and os.path.exists(output_filename):
            return output_filename
        else:
            LOGGER.error(f"Video cutting failed: {stderr.decode()}")
            return None
    except Exception as e:
        LOGGER.error(f"Error cutting video: {e}")
        return None

def get_file_size(filepath):
    try:
        if os.path.exists(filepath):
            return os.path.getsize(filepath)
        return 0
    except Exception as e:
        LOGGER.error(f"Error getting file size: {e}")
        return 0

def format_bytes(bytes_size):
    try:
        if not bytes_size or bytes_size <= 0:
            return "0 B"
        bytes_size = safe_float_convert(bytes_size)
        if bytes_size <= 0:
            return "0 B"
        size_names = ("B", "KB", "MB", "GB", "TB")
        i = int(math.floor(math.log(bytes_size, 1024)))
        i = min(i, len(size_names) - 1)
        p = math.pow(1024, i)
        s = round(bytes_size / p, 2)
        return f"{s} {size_names[i]}"
    except Exception as e:
        LOGGER.error(f"Error formatting bytes: {e}")
        return "0 B"

def cleanup_temp_files(file_paths):
    for filepath in file_paths:
        try:
            if filepath and os.path.exists(filepath):
                os.remove(filepath)
                LOGGER.info(f"Cleaned up: {filepath}")
        except Exception as e:
            LOGGER.warning(f"Could not clean up {filepath}: {e}")

def validate_video_file(filepath):
    try:
        if not os.path.exists(filepath):
            return False, "File does not exist"
        if get_file_size(filepath) == 0:
            return False, "File is empty"
        cmd = ['ffprobe', '-v', 'quiet', '-select_streams', 'v:0', '-show_entries', 'stream=codec_type', '-of', 'csv=p=0', filepath]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and "video" in result.stdout:
            return True, "Valid video file"
        else:
            return False, "Not a valid video file"
    except subprocess.TimeoutExpired:
        return False, "Validation timeout"
    except Exception as e:
        return False, f"Validation error: {e}"

# =================== Main convert_video1 Function ===================

async def convert_video1(video_file, output_directory, total_time, bot, message, chan_msg, watermark_url='https://i.ibb.co/fzr6BVZT/jsorg.jpg'):
    if not os.path.exists(video_file):
        LOGGER.error(f"Video file not found: {video_file}")
        return None

    total_time_safe = safe_float_convert(total_time)
    if total_time_safe == 0:
        total_time_safe = get_duration(video_file)
    if total_time_safe == 0:
        LOGGER.error("Could not determine video duration")
        return None

    try:
        os.makedirs(output_directory, exist_ok=True)
        kk = os.path.basename(video_file)
        name, ext = os.path.splitext(kk)
        temp_output = os.path.join(output_directory, f"{name}_temp.mkv")
        final_output = os.path.join(output_directory, f"{name}.mkv")
        progress_file = os.path.join(output_directory, "progress.txt")
        status_file = os.path.join(output_directory, "status.json")

        with open(progress_file, 'w') as f:
            f.write("")

        if not crf:
            crf.append("24")
        if not codec:
            codec.append("libx264")
        if not resolution:
            resolution.append("1920x1080")
        if not preset:
            preset.append("veryfast")
        if not audio_b:
            audio_b.append("35k")

        cmd = [
            'ffmpeg', '-hide_banner', '-loglevel', 'warning', '-progress', progress_file,
            '-i', video_file, '-i', watermark_url,
            '-filter_complex', '[1:v]colorkey=0x000000:0.1:0.1[wm]; [0:v][wm]overlay=10:10',
            '-map', '0:a?', '-map', '0:s?', '-c:v', codec[0],
            '-crf', crf[0], '-preset', preset[0], '-b:v', '150k',
            '-c:a', 'libopus', '-b:a', audio_b[0], '-pix_fmt', 'yuv420p', '-s', resolution[0],
            '-metadata', 'title=', '-y', temp_output
        ]

        COMPRESSION_START_TIME = time.time()
        process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        LOGGER.info(f"FFmpeg process started PID: {process.pid}")
        pid_list.insert(0, process.pid)

        status_data = {"pid": process.pid, "message": message.id}
        with open(status_file, 'w') as f:
            json.dump(status_data, f, indent=2)

        try:
            progress_msg = await bot.send_message(chat_id=message.chat.id, text="Starting compression...", reply_to_message_id=message.id)
        except:
            progress_msg = None

        encoding_complete = False
        last_update_time = 0
        consecutive_errors = 0

        while True:
            try:
                await asyncio.sleep(PROGRESSUPDATEINTERVAL)

                if process.returncode is not None:
                    if process.returncode == 0:
                        encoding_complete = True
                    else:
                        LOGGER.error(f"FFmpeg exited with code: {process.returncode}")
                        try:
                            stderr_output = await process.stderr.read()
                            if stderr_output:
                                LOGGER.error(f"FFmpeg stderr: {stderr_output.decode()}")
                        except:
                            pass
                    break

                if time.time() - COMPRESSION_START_TIME > FFMPEGTIMEOUT:
                    LOGGER.error("Encoding timeout reached")
                    process.terminate()
                    break

                if not os.path.exists(progress_file):
                    continue

                with open(progress_file, 'r') as f:
                    content = f.read()
                if not content.strip():
                    continue

                frame_match = re.findall(r'frame=(\d+)', content)
                time_match = re.findall(r'out_time_ms=(\d+)', content)
                speed_match = re.findall(r'speed=([\d.]+)x?', content)
                progress_match = re.findall(r'progress=(\w+)', content)

                frame = safe_int_convert(frame_match[-1] if frame_match else '1', 1)
                elapsed_us = safe_int_convert(time_match[-1] if time_match else '0', 0)
                speed_str = speed_match[-1] if speed_match else '1'
                progress_status = progress_match[-1] if progress_match else ''

                speed = safe_float_convert(speed_str, 0.1)
                if speed == 0 or speed_str in ('N/A', '0'):
                    speed = 0.1

                if progress_status == 'end':
                    LOGGER.info("Encoding completed successfully")
                    encoding_complete = True
                    break

                elapsed_time = safe_float_convert(elapsed_us / 1000000.0)
                percentage = min(99, (elapsed_time / total_time_safe) * 100 if total_time_safe > 0 else 0)

                if speed > 0 and total_time_safe > elapsed_time:
                    remaining_time = (total_time_safe - elapsed_time) / speed
                    eta = TimeFormatter(remaining_time * 1000)
                else:
                    eta = "Calculating..."

                execution_time = TimeFormatter((time.time() - COMPRESSION_START_TIME) * 1000)
                progress_bar_length = 10
                filled_bars = int(percentage / 10)
                progress_str = f"{''.join(FINISHED_PROGRESS_STR for _ in range(filled_bars))}{''.join(UN_FINISHED_PROGRESS_STR for _ in range(progress_bar_length - filled_bars))}"

                stats = f"""Progress: {progress_str} {percentage:.1f}%
Execution Time: {execution_time}
ETA: {eta}
Speed: {speed:.2f}x
Frame: {frame}"""

                current_time = time.time()
                if current_time - last_update_time >= 15 and progress_msg:
                    try:
                        await progress_msg.edit_text(
                            text=stats,
                            reply_markup=InlineKeyboardMarkup(
                                [[InlineKeyboardButton("❌", callback_data=f"cancel_{process.pid}")]]
                            )
                        )
                        last_update_time = current_time
                        consecutive_errors = 0
                    except Exception as e:
                        consecutive_errors += 1
                        LOGGER.debug(f"Progress message update error: {e}")
                        if consecutive_errors >= 3:
                            progress_msg = None

            except asyncio.CancelledError:
                LOGGER.info("Encoding cancelled")
                process.terminate()
                break
            except Exception as e:
                LOGGER.error(f"Error in encoding loop: {e}")
                continue

        # Cleanup
        try:
            if process and process.returncode is None:
                process.terminate()
                try:
                    await asyncio.wait_for(process.wait(), timeout=10)
                except asyncio.TimeoutError:
                    process.kill()
            for filepath in (progress_file, status_file):
                if filepath and os.path.exists(filepath):
                    try:
                        os.remove(filepath)
                    except Exception:
                        pass
        except Exception as e:
            LOGGER.error(f"Cleanup error: {e}")

        if progress_msg:
            try:
                await progress_msg.delete()
            except Exception:
                pass

        if process and process.pid in pid_list:
            pid_list.remove(process.pid)

        if encoding_complete and os.path.exists(temp_output) and get_file_size(temp_output) > 10000:
            if os.path.exists(final_output):
                os.remove(final_output)
            os.rename(temp_output, final_output)
            return final_output
        else:
            LOGGER.error(f"Encoding failed - Return code: {process.returncode if process else 'Unknown'}")
            LOGGER.error(f"Output file exists: {os.path.exists(temp_output)}")
            LOGGER.error(f"Output file size: {get_file_size(temp_output)}")
            if os.path.exists(temp_output):
                os.remove(temp_output)
            return None

    except Exception as e:
        LOGGER.error(f"Error in convert_video1: {e}")
        return None

async def convert_video(video_file, output_directory, total_time, bot, message, chan_msg, watermark_url='https://graph.org/file/b41a33cfdde9349b322b7.png'):
    return await convert_video1(video_file, output_directory, total_time, bot, message, chan_msg, watermark_url)

async def process_video(client, message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if chat_id not in AUTH_CHATS and user_id not in AUTH_USERS:
        return await message.reply("🚫 This bot only works in authorized chats.")
    
    watermark_url = await db.get_watermark_url(user_id)
    if not watermark_url:
        return await message.reply("⚠️ Set your watermark URL first using /us.")
