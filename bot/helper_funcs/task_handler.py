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
    get_duration,
    get_media_info_text
)
from bot.helper_funcs.display_progress import (
    progress_for_pyrogram,
    TimeFormatter,
    humanbytes
)
from bot.helper_funcs.utils import copy_to_dump_channel, upload_to_telegraph, output_handler
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

LOGGER = logging.getLogger(__name__)

async def execute_task(task_info):
    task_type = task_info.get('task_type')
    message = task_info.get('message')
    options = task_info.get('options', {})

    if task_type in ['compress', '480p', '720p', '1080p']:
        await handle_compression_task(message, task_type, options)
    elif task_type == 'extract_audio':
        await handle_extract_audio_task(message, options)
    elif task_type == 'extract_sub':
        await handle_extract_sub_task(message, options)
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
    # Fetch user settings from DB
    user_id = update.from_user.id if update.from_user else update.chat.id
    from bot.helper_funcs.database import get_user_data
    user_settings = await get_user_data(user_id)

    # Override resolution if specific task type is provided
    if task_type == '480p':
        user_settings['resolution'] = "480"
    elif task_type == '720p':
        user_settings['resolution'] = "720"
    elif task_type == '1080p':
        user_settings['resolution'] = "1080"
    elif 'resolution' in options:
        user_settings['resolution'] = options['resolution']

    # Special handling for "All" resolution if generic "compress" task is called
    if user_settings.get('resolution') == 'All' and task_type == 'compress':
        from bot.helper_funcs.utils import add_to_queue
        await add_to_queue(update, "480p", options)
        await add_to_queue(update, "720p", options)
        await add_to_queue(update, "1080p", options)
        return

    from bot.plugins.incoming_message_fn import incoming_compress_message_f
    await incoming_compress_message_f(update, user_settings=user_settings)

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
            await output_handler(
                bot=bot,
                update=message,
                output_path=audio_path,
                input_path=video_path,
                sent_message=sent_message
            )
        else:
            await sent_message.edit_text("❌ Audio extraction failed.")
            if video_path and os.path.exists(video_path): os.remove(video_path)
    except Exception as e:
        await sent_message.edit_text(f"❌ Error: {e}")

async def handle_extract_sub_task(message, options):
    sent_message = await bot.send_message(chat_id=message.chat.id, text="Dᴏᴡɴʟᴏᴀᴅɪɴɢ ꜰᴏʀ ꜱᴜʙᴛɪᴛʟᴇ ᴇxᴛʀᴀᴄᴛɪᴏɴ...📥", reply_to_message_id=message.id)
    try:
        video_path = await bot.download_media(message=message, progress=progress_for_pyrogram, progress_args=(bot, "Dᴏᴡɴʟᴏᴀᴅɪɴɢ...📥", sent_message, time.time()))
        if not video_path:
            return await sent_message.edit_text("❌ Download failed.")

        await sent_message.edit_text("📝 E𝗑𝗍𝗋𝖺𝖼𝗍𝗂𝗇𝗀 𝗌𝗎𝖻𝗍𝗂𝗍𝗅𝖾𝗌...⚙️")
        from bot.helper_funcs.ffmpeg import extract_subtitles
        sub_path = await extract_subtitles(video_path, DOWNLOAD_LOCATION)

        if sub_path:
            await output_handler(
                bot=bot,
                update=message,
                output_path=sub_path,
                input_path=video_path,
                sent_message=sent_message
            )
        else:
            await sent_message.edit_text("❌ Subtitle extraction failed. Make sure the video has subtitle streams.")
            if video_path and os.path.exists(video_path): os.remove(video_path)
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
            await output_handler(
                bot=bot,
                update=message,
                output_path=output_path,
                input_path=video_path,
                sent_message=sent_message
            )
            if audio_path and os.path.exists(audio_path): os.remove(audio_path)
        else:
            await sent_message.edit_text("❌ Adding audio failed.")
            for p in [video_path, audio_path]:
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
            await output_handler(
                bot=bot,
                update=message,
                output_path=output_path,
                input_path=video_path,
                sent_message=sent_message
            )
        else:
            await sent_message.edit_text("❌ Removing audio failed.")
            if video_path and os.path.exists(video_path): os.remove(video_path)
    except Exception as e:
        await sent_message.edit_text(f"❌ Error: {e}")

async def handle_subtitles_task(message, options, sub_type):
    sub_message = options.get('sub_message')
    sent_message = await bot.send_message(chat_id=message.chat.id, text="Dᴏᴡɴʟᴏᴀᴅɪɴɢ ꜰɪʟᴇꜱ...📥", reply_to_message_id=message.id)
    try:
        video_path = await bot.download_media(message=message, progress=progress_for_pyrogram, progress_args=(bot, "Dᴏᴡɴʟᴏᴀᴅɪɴɢ 𝗏𝗂𝖽𝖾𝗈...📥", sent_message, time.time()))
        sub_path = await bot.download_media(message=sub_message, progress=progress_for_pyrogram, progress_args=(bot, "Dᴏᴡɴʟᴏᴀᴅɪɴɢ 𝗌𝗎𝖻𝗌...📥", sent_message, time.time()))

        if not video_path or not sub_path: return await sent_message.edit_text("❌ Download failed.")

        user_id = message.from_user.id if message.from_user else message.chat.id
        from bot.helper_funcs.database import get_user_data
        user_settings = await get_user_data(user_id)

        await sent_message.edit_text(f"📝 A𝖽𝖽𝗂𝗇𝗀 {sub_type} 𝗌𝗎𝖻𝗍𝗂𝗍𝗅𝖾𝗌...⚙️")
        from bot.helper_funcs.ffmpeg import add_soft_subtitles, add_hard_subtitles
        if sub_type == "soft":
            output_path = await add_soft_subtitles(video_path, sub_path, DOWNLOAD_LOCATION)
        else:
            output_path = await add_hard_subtitles(video_path, sub_path, DOWNLOAD_LOCATION, bot, sent_message, settings=user_settings)

        if output_path:
            await output_handler(
                bot=bot,
                update=message,
                output_path=output_path,
                input_path=video_path,
                sent_message=sent_message
            )
            if sub_path and os.path.exists(sub_path): os.remove(sub_path)
        else:
            await sent_message.edit_text(f"❌ Adding {sub_type} subtitles failed.")
            for p in [video_path, sub_path]:
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
            await output_handler(
                bot=bot,
                update=message,
                output_path=output_path,
                input_path=video_path,
                sent_message=sent_message
            )
        else:
            await sent_message.edit_text("❌ Removing subtitles failed.")
            if video_path and os.path.exists(video_path): os.remove(video_path)
    except Exception as e:
        await sent_message.edit_text(f"❌ Error: {e}")

async def handle_trim_task(message, options):
    start_time = options.get('start_time')
    end_time = options.get('end_time')
    sent_message = await bot.send_message(chat_id=message.chat.id, text="Dᴏᴡɴʟᴏᴀᴅɪɴɢ...📥", reply_to_message_id=message.id)
    try:
        video_path = await bot.download_media(message=message, progress=progress_for_pyrogram, progress_args=(bot, "Dᴏᴡɴʟᴏᴀᴅɪɴɢ...📥", sent_message, time.time()))
        if not video_path: return await sent_message.edit_text("❌ Download failed.")

        user_id = message.from_user.id if message.from_user else message.chat.id
        from bot.helper_funcs.database import get_user_data
        user_settings = await get_user_data(user_id)

        await sent_message.edit_text(f"✂️ T𝗋𝗂𝗆𝗆𝗂𝗇𝗀 𝗏𝗂𝖽𝖾𝗈 ({start_time} - {end_time})...⚙️")
        from bot.helper_funcs.ffmpeg import cut_video
        output_path = await cut_video(video_path, DOWNLOAD_LOCATION, start_time, end_time, bot, sent_message, settings=user_settings)

        if output_path:
            await output_handler(
                bot=bot,
                update=message,
                output_path=output_path,
                input_path=video_path,
                sent_message=sent_message
            )
        else:
            await sent_message.edit_text("❌ Trimming failed.")
            if video_path and os.path.exists(video_path): os.remove(video_path)
    except Exception as e:
        await sent_message.edit_text(f"❌ Error: {e}")

async def handle_mediainfo_task(message, options):
    sent_message = await bot.send_message(chat_id=message.chat.id, text="ꜰᴇᴛᴄʜɪɴɢ ᴍᴇᴅɪᴀ ɪɴꜰᴏ...📥", reply_to_message_id=message.id)
    try:
        # Download only first 10MB
        video_path = os.path.join(DOWNLOAD_LOCATION, f"mi_{int(time.time())}.mp4")

        downloaded_size = 0
        MAX_SIZE = 10 * 1024 * 1024 # 10MB

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

        # We want plain text for Telegraph <pre>
        info_text = await get_media_info_text(video_path)
        # Strip HTML tags for Telegraph <pre>
        # Only if it actually contains HTML, but my new formatter doesn't
        plain_info = re.sub(r'<[^>]*>', '', info_text)

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
    file_messages = options.get('video_messages', [])
    if not file_messages:
        return await bot.send_message(chat_id=message.chat.id, text="❌ No files found for merge.")

    sent_message = await bot.send_message(chat_id=message.chat.id, text=f"Dᴏᴡɴʟᴏᴀᴅɪɴɢ {len(file_messages)} 𝖿𝗂𝗅𝖾𝗌 𝖿𝗈𝗋 𝗆𝖾𝗋𝗀𝖾...📥", reply_to_message_id=message.id)

    downloaded_files = []
    try:
        for i, msg in enumerate(file_messages):
            await sent_message.edit_text(f"Dᴏᴡɴʟᴏᴀᴅɪɴɢ 𝖿𝗂𝗅𝖾 {i+1}/{len(file_messages)}...📥")
            file_path = await bot.download_media(
                message=msg,
                progress=progress_for_pyrogram,
                progress_args=(bot, f"Dᴏᴡɴʟᴏᴀᴅɪɴɢ 𝖿𝗂𝗅𝖾 {i+1}...📥", sent_message, time.time())
            )
            if file_path:
                downloaded_files.append(file_path)
            else:
                await sent_message.edit_text(f"❌ Failed to download file {i+1}. Aborting.")
                for p in downloaded_files:
                    if os.path.exists(p): os.remove(p)
                return

        await sent_message.edit_text("🎬 C𝖺𝗅𝖼𝗎𝗅𝖺𝗍𝗂𝗇𝗀 𝖽𝗎𝗋𝖺𝗍𝗂𝗈𝗇...⚙️")
        from bot.helper_funcs.ffmpeg import get_duration, merge_videos
        total_duration = 0
        for f_path in downloaded_files:
            total_duration += get_duration(f_path)

        if total_duration == 0:
            total_duration = 1 # Avoid division by zero

        # Determine output extension based on first file
        is_audio = False
        first_msg = file_messages[0]
        if first_msg.audio or (first_msg.document and first_msg.document.mime_type and first_msg.document.mime_type.startswith("audio/")):
            is_audio = True

        ext = ".mp3" if is_audio else ".mp4"
        requested_output_path = os.path.join(DOWNLOAD_LOCATION, f"merged_{int(time.time())}{ext}")

        result = await merge_videos(downloaded_files, requested_output_path, bot, sent_message, total_duration)

        if result and os.path.exists(result):
            # Use centralized output_handler
            await output_handler(
                bot=bot,
                update=message,
                output_path=result,
                sent_message=sent_message
            )
        else:
            await sent_message.edit_text("❌ Merging failed.")

    except Exception as e:
        LOGGER.error(f"Error in handle_merge_task: {e}")
        try:
            await sent_message.edit_text(f"❌ Error: {e}")
        except:
            pass
    finally:
        for p in downloaded_files:
            if p and os.path.exists(p): os.remove(p)
