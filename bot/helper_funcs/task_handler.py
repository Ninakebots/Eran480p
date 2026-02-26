import logging
import os
import time
import datetime
import json
import re
from bot import (
    DOWNLOAD_LOCATION,
    LOGGER,
    app as bot,
    LOG_CHANNEL,
    crf as global_crf,
    resolution as global_resolution,
    audio_b as global_audio_b,
    preset as global_preset,
    codec as global_codec
)
from bot.localisation import Localisation
from bot.helper_funcs.ffmpeg import (
    media_info,
    take_screen_shot,
    get_duration
)
from bot.helper_funcs.display_progress import (
    progress_for_pyrogram,
    TimeFormatter,
    humanbytes
)
from bot.helper_funcs.utils import copy_to_dump_channel

LOGGER = logging.getLogger(__name__)

async def execute_task(task_info):
    task_type = task_info.get('task_type')
    message = task_info.get('message')
    options = task_info.get('options', {})

    if task_type in ['compress', '480p', '720p', '1080p']:
        await handle_compression_task(message, task_type, options)
    elif task_type == 'extract_audio':
        await handle_extract_audio_task(message, options)
    elif task_type == 'add_audio':
        await handle_add_audio_task(message, options)
    elif task_type == 'remove_audio':
        await handle_remove_audio_task(message, options)
    elif task_type == 'add_soft_sub':
        await handle_subtitles_task(message, options, "soft")
    elif task_type == 'add_hard_sub':
        await handle_subtitles_task(message, options, "hard")
    elif task_type == 'remove_sub':
        await handle_remove_subtitles_task(message, options)
    elif task_type == 'trim':
        await handle_trim_task(message, options)
    elif task_type == 'mediainfo':
        await handle_mediainfo_task(message, options)
    elif task_type == 'merge':
        await handle_merge_task(message, options)
    else:
        LOGGER.warning(f"Unknown task type: {task_type}")

async def handle_compression_task(update, task_type, options):
    # Similar to incoming_compress_message_f but with options
    # Set temporary globals if needed or pass to convert_video1

    if task_type == '480p':
        res = "854x480"
    elif task_type == '720p':
        res = "1280x720"
    elif task_type == '1080p':
        res = "1920x1080"
    else:
        res = options.get('resolution', global_resolution[0] if global_resolution else "1280x720")

    # Temporarily override globals for this task
    # This is a bit hacky but consistent with existing code
    old_res_existed = len(global_resolution) > 0
    old_res = global_resolution[0] if old_res_existed else "1280x720"

    if old_res_existed:
        global_resolution[0] = res
    else:
        global_resolution.append(res)

    from bot.plugins.incoming_message_fn import incoming_compress_message_f
    try:
        await incoming_compress_message_f(update)
    finally:
        # Restore global
        if old_res_existed:
            global_resolution[0] = old_res
        else:
            global_resolution.clear()

async def handle_extract_audio_task(message, options):
    sent_message = await bot.send_message(chat_id=message.chat.id, text="Dᴏᴡɴʟᴏᴀᴅɪɴɢ ꜰᴏʀ ᴀᴜᴅɪᴏ ᴇxᴛʀᴀᴄᴛɪᴏɴ...📥", reply_to_message_id=message.id)
    try:
        video_path = await bot.download_media(message=message, progress=progress_for_pyrogram, progress_args=(bot, "Dᴏᴡɴʟᴏᴀᴅɪɴɢ...📥", sent_message, time.time()))
        if not video_path:
            return await sent_message.edit_text("❌ Download failed.")

        await sent_message.edit_text("🎧 E𝗑𝗍𝗋𝖺𝖼𝗍𝗂𝗇𝗀 𝖺𝗎𝖽𝗂𝗈...⚙️")
        from bot.helper_funcs.ffmpeg import extract_audio
        audio_path = await extract_audio(video_path, DOWNLOAD_LOCATION)

        if audio_path:
            await sent_message.edit_text("📤 U𝗉𝗅𝗈𝖺𝖽𝗂𝗇𝗀 𝖺𝗎𝖽𝗂𝗈...")
            sent_audio = await bot.send_audio(chat_id=message.chat.id, audio=audio_path, reply_to_message_id=message.id)
            if sent_audio:
                await copy_to_dump_channel(bot, sent_audio, message.from_user.id if message.from_user else "Unknown")
            await sent_message.delete()
        else:
            await sent_message.edit_text("❌ Audio extraction failed.")

        if video_path and os.path.exists(video_path): os.remove(video_path)
        if audio_path and os.path.exists(audio_path): os.remove(audio_path)
    except Exception as e:
        await sent_message.edit_text(f"❌ Error: {e}")

async def handle_add_audio_task(message, options):
    audio_message = options.get('audio_message')
    sent_message = await bot.send_message(chat_id=message.chat.id, text="Dᴏᴡɴʟᴏᴀᴅɪɴɢ ꜰɪʟᴇꜱ...📥", reply_to_message_id=message.id)
    try:
        video_path = await bot.download_media(message=message, progress=progress_for_pyrogram, progress_args=(bot, "Dᴏᴡɴʟᴏᴀᴅɪɴɢ 𝗏𝗂𝖽𝖾𝗈...📥", sent_message, time.time()))
        audio_path = await bot.download_media(message=audio_message, progress=progress_for_pyrogram, progress_args=(bot, "Dᴏᴡɴʟᴏᴀᴅɪɴɢ 𝖺𝗎𝖽𝗂𝗈...📥", sent_message, time.time()))

        if not video_path or not audio_path:
            return await sent_message.edit_text("❌ Download failed.")

        await sent_message.edit_text("🎵 A𝖽𝖽𝗂𝗇𝗀 𝖺𝗎𝖽𝗂𝗈...⚙️")
        from bot.helper_funcs.ffmpeg import add_audio
        output_path = await add_audio(video_path, audio_path, DOWNLOAD_LOCATION)

        if output_path:
            await sent_message.edit_text("📤 U𝗉𝗅𝗈𝖺𝖽𝗂𝗇𝗀 𝗋𝖾𝗌𝗎𝗅𝗍...")
            sent_video = await bot.send_video(chat_id=message.chat.id, video=output_path, reply_to_message_id=message.id)
            if sent_video:
                await copy_to_dump_channel(bot, sent_video, message.from_user.id if message.from_user else "Unknown")
            await sent_message.delete()
        else:
            await sent_message.edit_text("❌ Adding audio failed.")

        for p in [video_path, audio_path, output_path]:
            if p and os.path.exists(p): os.remove(p)
    except Exception as e:
        await sent_message.edit_text(f"❌ Error: {e}")

async def handle_remove_audio_task(message, options):
    sent_message = await bot.send_message(chat_id=message.chat.id, text="Dᴏᴡɴʟᴏᴀᴅɪɴɢ...📥", reply_to_message_id=message.id)
    try:
        video_path = await bot.download_media(message=message, progress=progress_for_pyrogram, progress_args=(bot, "Dᴏᴡɴʟᴏᴀᴅɪɴɢ...📥", sent_message, time.time()))
        if not video_path: return await sent_message.edit_text("❌ Download failed.")

        await sent_message.edit_text("🔇 R𝖾𝗆𝗈𝗏𝗂𝗇𝗀 𝖺𝗎𝖽𝗂𝗈...⚙️")
        from bot.helper_funcs.ffmpeg import remove_audio
        output_path = await remove_audio(video_path, DOWNLOAD_LOCATION)

        if output_path:
            sent_video = await bot.send_video(chat_id=message.chat.id, video=output_path, reply_to_message_id=message.id)
            if sent_video:
                await copy_to_dump_channel(bot, sent_video, message.from_user.id if message.from_user else "Unknown")
            await sent_message.delete()
        else:
            await sent_message.edit_text("❌ Removing audio failed.")
        if video_path and os.path.exists(video_path): os.remove(video_path)
        if output_path and os.path.exists(output_path): os.remove(output_path)
    except Exception as e:
        await sent_message.edit_text(f"❌ Error: {e}")

async def handle_subtitles_task(message, options, sub_type):
    sub_message = options.get('sub_message')
    sent_message = await bot.send_message(chat_id=message.chat.id, text="Dᴏᴡɴʟᴏᴀᴅɪɴɢ ꜰɪʟᴇꜱ...📥", reply_to_message_id=message.id)
    try:
        video_path = await bot.download_media(message=message, progress=progress_for_pyrogram, progress_args=(bot, "Dᴏᴡɴʟᴏᴀᴅɪɴɢ 𝗏𝗂𝖽𝖾𝗈...📥", sent_message, time.time()))
        sub_path = await bot.download_media(message=sub_message, progress=progress_for_pyrogram, progress_args=(bot, "Dᴏᴡɴʟᴏᴀᴅɪɴɢ 𝗌𝗎𝖻𝗌...📥", sent_message, time.time()))

        if not video_path or not sub_path: return await sent_message.edit_text("❌ Download failed.")

        await sent_message.edit_text(f"📝 A𝖽𝖽𝗂𝗇𝗀 {sub_type} 𝗌𝗎𝖻𝗍𝗂𝗍𝗅𝖾𝗌...⚙️")
        from bot.helper_funcs.ffmpeg import add_soft_subtitles, add_hard_subtitles
        if sub_type == "soft":
            output_path = await add_soft_subtitles(video_path, sub_path, DOWNLOAD_LOCATION)
        else:
            output_path = await add_hard_subtitles(video_path, sub_path, DOWNLOAD_LOCATION, bot, sent_message)

        if output_path:
            sent_doc = await bot.send_document(chat_id=message.chat.id, document=output_path, reply_to_message_id=message.id)
            if sent_doc:
                await copy_to_dump_channel(bot, sent_doc, message.from_user.id if message.from_user else "Unknown")
            await sent_message.delete()
        else:
            await sent_message.edit_text(f"❌ Adding {sub_type} subtitles failed.")
        for p in [video_path, sub_path, output_path]:
            if p and os.path.exists(p): os.remove(p)
    except Exception as e:
        await sent_message.edit_text(f"❌ Error: {e}")

async def handle_remove_subtitles_task(message, options):
    sent_message = await bot.send_message(chat_id=message.chat.id, text="Dᴏᴡɴʟᴏᴀᴅɪɴɢ...📥", reply_to_message_id=message.id)
    try:
        video_path = await bot.download_media(message=message, progress=progress_for_pyrogram, progress_args=(bot, "Dᴏᴡɴʟᴏᴀᴅɪɴɢ...📥", sent_message, time.time()))
        if not video_path: return await sent_message.edit_text("❌ Download failed.")

        await sent_message.edit_text("✂️ R𝖾𝗆𝗈𝗏𝗂𝗇𝗀 𝗌𝗎𝖻𝗍𝗂𝗍𝗅𝖾𝗌...⚙️")
        from bot.helper_funcs.ffmpeg import remove_subtitles
        output_path = await remove_subtitles(video_path, DOWNLOAD_LOCATION)

        if output_path:
            sent_video = await bot.send_video(chat_id=message.chat.id, video=output_path, reply_to_message_id=message.id)
            if sent_video:
                await copy_to_dump_channel(bot, sent_video, message.from_user.id if message.from_user else "Unknown")
            await sent_message.delete()
        else:
            await sent_message.edit_text("❌ Removing subtitles failed.")
        if video_path and os.path.exists(video_path): os.remove(video_path)
        if output_path and os.path.exists(output_path): os.remove(output_path)
    except Exception as e:
        await sent_message.edit_text(f"❌ Error: {e}")

async def handle_trim_task(message, options):
    start_time = options.get('start_time')
    end_time = options.get('end_time')
    sent_message = await bot.send_message(chat_id=message.chat.id, text="Dᴏᴡɴʟᴏᴀᴅɪɴɢ...📥", reply_to_message_id=message.id)
    try:
        video_path = await bot.download_media(message=message, progress=progress_for_pyrogram, progress_args=(bot, "Dᴏᴡɴʟᴏᴀᴅɪɴɢ...📥", sent_message, time.time()))
        if not video_path: return await sent_message.edit_text("❌ Download failed.")

        await sent_message.edit_text(f"✂️ T𝗋𝗂𝗆𝗆𝗂𝗇𝗀 𝗏𝗂𝖽𝖾𝗈 ({start_time} - {end_time})...⚙️")
        from bot.helper_funcs.ffmpeg import cult_small_video
        output_path = await cult_small_video(video_path, DOWNLOAD_LOCATION, start_time, end_time, bot, sent_message)

        if output_path:
            sent_video = await bot.send_video(chat_id=message.chat.id, video=output_path, reply_to_message_id=message.id)
            if sent_video:
                await copy_to_dump_channel(bot, sent_video, message.from_user.id if message.from_user else "Unknown")
            await sent_message.delete()
        else:
            await sent_message.edit_text("❌ Trimming failed.")
        if video_path and os.path.exists(video_path): os.remove(video_path)
        if output_path and os.path.exists(output_path): os.remove(output_path)
    except Exception as e:
        await sent_message.edit_text(f"❌ Error: {e}")

async def handle_mediainfo_task(message, options):
    sent_message = await bot.send_message(chat_id=message.chat.id, text="ꜰᴇᴛᴄʜɪɴɢ ᴍᴇᴅɪᴀ ɪɴꜰᴏ...📥", reply_to_message_id=message.id)
    try:
        # Download only first 5MB
        video_path = os.path.join(DOWNLOAD_LOCATION, f"mi_{int(time.time())}.mp4")

        downloaded_size = 0
        MAX_SIZE = 5 * 1024 * 1024 # 5MB

        try:
            async for chunk in bot.stream_media(message):
                with open(video_path, "ab") as f:
                    f.write(chunk)
                downloaded_size += len(chunk)
                if downloaded_size >= MAX_SIZE:
                    break
        except Exception as e:
            LOGGER.error(f"Error streaming for mediainfo: {e}")

        if not os.path.exists(video_path) or os.path.getsize(video_path) == 0:
            return await sent_message.edit_text("❌ Failed to fetch partial file for MediaInfo.")

        from bot.helper_funcs.ffmpeg import get_media_info_text
        # We want plain text for Telegraph <pre>
        info_text = await get_media_info_text(video_path)
        # Strip HTML tags for Telegraph <pre>
        plain_info = re.sub(r'<[^>]*>', '', info_text)

        from bot.helper_funcs.utils import upload_to_telegraph
        from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

        title = "Media Info"
        if message.video and message.video.file_name:
            title = message.video.file_name
        elif message.document and message.document.file_name:
            title = message.document.file_name

        telegraph_url = await upload_to_telegraph(f"Media Info - {title}", plain_info)

        if telegraph_url:
            await sent_message.edit_text(
                f"📊 **Media Info Generated!**",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("View MediaInfo", url=telegraph_url)]])
            )
        else:
            await sent_message.edit_text("❌ Failed to upload MediaInfo to Telegraph.")

        if video_path and os.path.exists(video_path): os.remove(video_path)
    except Exception as e:
        LOGGER.error(f"Error in handle_mediainfo_task: {e}")
        await sent_message.edit_text(f"❌ Error: {e}")

async def handle_merge_task(message, options):
    video_messages = options.get('video_messages', [])
    if not video_messages:
        return await bot.send_message(chat_id=message.chat.id, text="❌ No videos found for merge.")

    sent_message = await bot.send_message(chat_id=message.chat.id, text=f"Dᴏᴡɴʟᴏᴀᴅɪɴɢ {len(video_messages)} 𝗏𝗂𝖽𝖾𝗈𝗌 𝖿𝗈𝗋 𝗆𝖾𝗋𝗀𝖾...📥", reply_to_message_id=message.id)

    downloaded_videos = []
    try:
        for i, msg in enumerate(video_messages):
            await sent_message.edit_text(f"Dᴏᴡɴʟᴏᴀᴅɪɴɢ 𝗏𝗂𝖽𝖾𝗈 {i+1}/{len(video_messages)}...📥")
            video_path = await bot.download_media(
                message=msg,
                progress=progress_for_pyrogram,
                progress_args=(bot, f"Dᴏᴡɴʟᴏᴀᴅɪɴɢ 𝗏𝗂𝖽𝖾𝗈 {i+1}...📥", sent_message, time.time())
            )
            if video_path:
                downloaded_videos.append(video_path)
            else:
                await sent_message.edit_text(f"❌ Failed to download video {i+1}. Aborting.")
                for p in downloaded_videos:
                    if os.path.exists(p): os.remove(p)
                return

        await sent_message.edit_text("🎬 C𝖺𝗅𝖼𝗎𝗅𝖺𝗍𝗂𝗇𝗀 𝖽𝗎𝗋𝖺𝗍𝗂𝗈𝗇...⚙️")
        from bot.helper_funcs.ffmpeg import get_duration, merge_videos
        total_duration = 0
        for vid in downloaded_videos:
            total_duration += get_duration(vid)

        if total_duration == 0:
            total_duration = 1 # Avoid division by zero

        output_path = os.path.join(DOWNLOAD_LOCATION, f"merged_{int(time.time())}.mp4")

        result = await merge_videos(downloaded_videos, output_path, bot, sent_message, total_duration)

        if result and os.path.exists(result):
            await sent_message.edit_text("📤 U𝗉𝗅𝗈𝖺𝖽𝗂𝗇𝗀 𝗆𝖾𝗋𝗀𝖾𝖽 𝗏𝗂𝖽𝖾𝗈...")
            sent_video = await bot.send_video(
                chat_id=message.chat.id,
                video=result,
                caption=f"✅ Merged {len(video_messages)} videos successfully!",
                reply_to_message_id=message.id,
                progress=progress_for_pyrogram,
                progress_args=(bot, "Uᴘʟᴏᴀᴅɪɴɢ...📤", sent_message, time.time())
            )
            if sent_video:
                await copy_to_dump_channel(bot, sent_video, message.from_user.id if message.from_user else "Unknown")
            await sent_message.delete()
        else:
            await sent_message.edit_text("❌ Merging failed.")

    except Exception as e:
        LOGGER.error(f"Error in handle_merge_task: {e}")
        await sent_message.edit_text(f"❌ Error: {e}")
    finally:
        for p in downloaded_videos:
            if p and os.path.exists(p): os.remove(p)
        if 'output_path' in locals() and os.path.exists(output_path):
            os.remove(output_path)
