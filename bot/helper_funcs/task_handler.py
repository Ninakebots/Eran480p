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
    get_thumbnail,
    get_media_info_text
)
from bot.helper_funcs.display_progress import (
    progress_for_pyrogram,
    TimeFormatter,
    humanbytes
)
from bot.helper_funcs.output import copy_to_dump_channel, upload_to_telegraph, output_handler
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

LOGGER = logging.getLogger(__name__)

async def execute_task(task_info):
    task_type = task_info.get('task_type')
    message = task_info.get('message')
    options = task_info.get('options', {})

    if task_type in ['compress', '480p', '720p', '1080p']:
        await handle_compression_task(message, task_type, options)
    elif task_type == 'all_resolutions':
        await handle_all_resolutions_task(message, options)
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

async def CompressVideo(bot, query, ffmpegcode, c_thumb=None):
    """Directly compress video from callback query with custom ffmpeg code."""
    update = query.message
    # Callback query messages are usually the bot's message.
    # The actual media is in the message it's replying to.
    media_message = update.reply_to_message
    if not media_message:
        return await query.answer("❌ Media message not found.", show_alert=True)

    sent_message = await bot.send_message(chat_id=update.chat.id, text=Localisation.DOWNLOAD_START, reply_to_message_id=media_message.id)
    await query.answer("🚀 Starting Custom Compression...")

    try:
        d_start = time.time()
        os.makedirs(DOWNLOAD_LOCATION, exist_ok=True)

        video_path = await bot.download_media(
            message=media_message,
            progress=progress_for_pyrogram,
            progress_args=(bot, Localisation.DOWNLOAD_START, sent_message, d_start)
        )

        if not video_path or not os.path.exists(video_path):
            return await sent_message.edit_text("❌ Download failed.")

        download_time = TimeFormatter((time.time() - d_start) * 1000)
        duration = get_duration(video_path)

        await sent_message.edit_text(Localisation.COMPRESS_START)
        c_start = time.time()

        from bot.helper_funcs.ffmpeg import convert_video_custom
        output_file = await convert_video_custom(video_path, DOWNLOAD_LOCATION, duration, bot, sent_message, ffmpegcode)

        encoding_time = TimeFormatter((time.time() - c_start) * 1000)

        if output_file and os.path.exists(output_file):
            await output_handler(
                bot=bot,
                update=media_message,
                output_path=output_file,
                download_time=download_time,
                encoding_time=encoding_time,
                thumb_path=c_thumb,
                input_path=video_path,
                sent_message=sent_message
            )
        else:
            await sent_message.edit_text("❌ Compression failed. Output file not generated.")
            if os.path.exists(video_path): os.remove(video_path)

    except Exception as e:
        LOGGER.error(f"Error in CompressVideo: {e}")
        await sent_message.edit_text(f"❌ Error: {e}")

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
        await handle_all_resolutions_task(update, options)
        return

    from bot.plugins.incoming_message_fn import incoming_compress_message_f
    await incoming_compress_message_f(update, user_settings=user_settings)

async def handle_all_resolutions_task(update, options):
    user_id = update.from_user.id if update.from_user else update.chat.id
    from bot.helper_funcs.database import get_user_data
    user_settings = await get_user_data(user_id)

    sent_message = await bot.send_message(chat_id=update.chat.id, text=Localisation.DOWNLOAD_START, reply_to_message_id=update.id)

    try:
        d_start = time.time()
        os.makedirs(DOWNLOAD_LOCATION, exist_ok=True)

        video_path = await bot.download_media(
            message=update,
            progress=progress_for_pyrogram,
            progress_args=(bot, Localisation.DOWNLOAD_START, sent_message, d_start)
        )

        if not video_path or not os.path.exists(video_path):
            return await sent_message.edit_text("❌ Download failed.")

        download_time = TimeFormatter((time.time() - d_start) * 1000)
        duration = get_duration(video_path)

        await sent_message.edit_text(Localisation.COMPRESS_START)
        c_start = time.time()

        from bot.helper_funcs.ffmpeg import convert_video_all
        output_files = await convert_video_all(video_path, DOWNLOAD_LOCATION, duration, bot, sent_message, user_settings)

        encoding_time = TimeFormatter((time.time() - c_start) * 1000)

        if not output_files:
            await sent_message.edit_text("❌ Multi-resolution encoding failed.")
            if os.path.exists(video_path): os.remove(video_path)
            return

        # Generate thumbnail for uploads
        thumb_path = os.path.join(DOWNLOAD_LOCATION, f"thumb_all_{int(time.time())}.jpg")
        thumb_path = get_thumbnail(video_path, thumb_path, time_offset=str(duration / 2))

        for out_file in output_files:
            await output_handler(
                bot=bot,
                update=update,
                output_path=out_file,
                download_time=download_time,
                encoding_time=encoding_time,
                thumb_path=thumb_path,
                input_path=None, # We'll clean up video_path manually after all uploads
                sent_message=None # Let it create new messages for each upload
            )

        if os.path.exists(video_path): os.remove(video_path)
        if thumb_path and os.path.exists(thumb_path): os.remove(thumb_path)
        await sent_message.delete()

    except Exception as e:
        LOGGER.error(f"Error in handle_all_resolutions_task: {e}")
        await sent_message.edit_text(f"❌ Error: {e}")

async def _process_media_handler(message, description, processing_func, *func_args, **func_kwargs):
    """Centralized helper for media processing tasks."""
    sent_message = await bot.send_message(chat_id=message.chat.id, text="Dᴏᴡɴʟᴏᴀᴅɪɴɢ...📥", reply_to_message_id=message.id)
    try:
        video_path = await bot.download_media(message=message, progress=progress_for_pyrogram, progress_args=(bot, "Dᴏᴡɴʟᴏᴀᴅɪɴɢ...📥", sent_message, time.time()))
        if not video_path: return await sent_message.edit_text("❌ Download failed.")

        await sent_message.edit_text(f"{description}...⚙️")
        output_path = await processing_func(video_path, DOWNLOAD_LOCATION, *func_args, **func_kwargs)

        if output_path:
            await output_handler(bot=bot, update=message, output_path=output_path, input_path=video_path, sent_message=sent_message)
        else:
            await sent_message.edit_text("❌ Processing failed.")
            if video_path and os.path.exists(video_path): os.remove(video_path)
    except Exception as e:
        LOGGER.error(f"Error in _process_media_handler: {e}")
        await sent_message.edit_text(f"❌ Error: {e}")

async def handle_extract_audio_task(message, options):
    from bot.helper_funcs.ffmpeg import extract_audio
    await _process_media_handler(message, "🎧 E𝗑𝗍𝗋𝖺𝖼𝗍𝗂𝗇𝗀 𝖺𝗎𝖽𝗂𝗈", extract_audio)

async def handle_extract_sub_task(message, options):
    from bot.helper_funcs.ffmpeg import extract_subtitles
    await _process_media_handler(message, "📝 E𝗑𝗍𝗋𝖺𝖼𝗍𝗂𝗇𝗀 𝗌𝗎𝖻𝗍𝗂𝗍𝗅𝖾𝗌", extract_subtitles)

async def handle_add_audio_task(message, options):
    audio_msg = options.get('audio_message')
    sent_message = await bot.send_message(chat_id=message.chat.id, text="Dᴏᴡɴʟᴏᴀᴅɪɴɢ ꜰɪʟᴇꜱ...📥", reply_to_message_id=message.id)
    try:
        v_path = await bot.download_media(message=message, progress=progress_for_pyrogram, progress_args=(bot, "Dᴏᴡɴʟᴏᴀᴅɪɴɢ 𝗏𝗂𝖽𝖾𝗈...📥", sent_message, time.time()))
        a_path = await bot.download_media(message=audio_msg, progress=progress_for_pyrogram, progress_args=(bot, "Dᴏᴡɴʟᴏᴀᴅɪɴɢ 𝖺𝗎𝖽𝗂𝗈...📥", sent_message, time.time()))
        if not v_path or not a_path: return await sent_message.edit_text("❌ Download failed.")

        await sent_message.edit_text("🎵 A𝖽𝖽𝗂𝗇𝗀 𝖺𝗎𝖽𝗂𝗈...⚙️")
        from bot.helper_funcs.ffmpeg import add_audio
        output_path = await add_audio(v_path, a_path, DOWNLOAD_LOCATION)

        if output_path:
            await output_handler(bot=bot, update=message, output_path=output_path, input_path=v_path, sent_message=sent_message)
        else: await sent_message.edit_text("❌ Adding audio failed.")
        if a_path and os.path.exists(a_path): os.remove(a_path)
    except Exception as e: await sent_message.edit_text(f"❌ Error: {e}")

async def handle_remove_audio_task(message, options):
    from bot.helper_funcs.ffmpeg import remove_audio
    await _process_media_handler(message, "🔇 R𝖾𝗆𝗈𝗏𝗂𝗇𝗀 𝖺𝗎𝖽𝗂𝗈", remove_audio)

async def handle_subtitles_task(message, options, sub_type):
    sub_msg = options.get('sub_message')
    sent_message = await bot.send_message(chat_id=message.chat.id, text="Dᴏᴡɴʟᴏᴀᴅɪɴɢ ꜰɪʟᴇꜱ...📥", reply_to_message_id=message.id)
    try:
        v_path = await bot.download_media(message=message, progress=progress_for_pyrogram, progress_args=(bot, "Dᴏᴡɴʟᴏᴀᴅɪɴɢ 𝗏𝗂𝖽𝖾𝗈...📥", sent_message, time.time()))
        s_path = await bot.download_media(message=sub_msg, progress=progress_for_pyrogram, progress_args=(bot, "Dᴏᴡɴʟᴏᴀᴅɪɴɢ 𝗌𝗎𝖻𝗌...📥", sent_message, time.time()))
        if not v_path or not s_path: return await sent_message.edit_text("❌ Download failed.")

        user_id = message.from_user.id if message.from_user else message.chat.id
        from bot.helper_funcs.database import get_user_data
        user_settings = await get_user_data(user_id)

        await sent_message.edit_text(f"📝 A𝖽𝖽𝗂𝗇𝗀 {sub_type} 𝗌𝗎𝖻𝗍𝗂𝗍𝗅𝖾𝗌...⚙️")
        from bot.helper_funcs.ffmpeg import add_soft_subtitles, add_hard_subtitles
        if sub_type == "soft": output_path = await add_soft_subtitles(v_path, s_path, DOWNLOAD_LOCATION)
        else: output_path = await add_hard_subtitles(v_path, s_path, DOWNLOAD_LOCATION, bot, sent_message, settings=user_settings)

        if output_path:
            await output_handler(bot=bot, update=message, output_path=output_path, input_path=v_path, sent_message=sent_message)
        else: await sent_message.edit_text(f"❌ Adding {sub_type} subtitles failed.")
        if s_path and os.path.exists(s_path): os.remove(s_path)
    except Exception as e: await sent_message.edit_text(f"❌ Error: {e}")

async def handle_remove_subtitles_task(message, options):
    from bot.helper_funcs.ffmpeg import remove_subtitles
    await _process_media_handler(message, "✂️ R𝖾𝗆𝗈𝗏𝗂𝗇𝗀 𝗌𝗎𝖻𝗍𝗂𝗍ʟ𝖾𝗌", remove_subtitles)

async def handle_trim_task(message, options):
    start_t, end_t = options.get('start_time'), options.get('end_time')
    user_id = message.from_user.id if message.from_user else message.chat.id
    from bot.helper_funcs.database import get_user_data
    user_settings = await get_user_data(user_id)
    from bot.helper_funcs.ffmpeg import cut_video

    # Explicit implementation for trim to ensure progress updates are passed correctly
    sent_message = await bot.send_message(chat_id=message.chat.id, text="Dᴏᴡɴʟᴏᴀᴅɪɴɢ...📥", reply_to_message_id=message.id)
    try:
        video_path = await bot.download_media(message=message, progress=progress_for_pyrogram, progress_args=(bot, "Dᴏᴡɴʟᴏᴀᴅɪɴɢ...📥", sent_message, time.time()))
        if not video_path: return await sent_message.edit_text("❌ Download failed.")

        await sent_message.edit_text(f"✂️ T𝗋𝗂𝗆𝗆𝗂𝗇𝗀 𝗏𝗂𝖽𝖾𝗈 ({start_t} - {end_t})...⚙️")
        output_path = await cut_video(video_path, DOWNLOAD_LOCATION, start_t, end_t, bot, sent_message, settings=user_settings)

        if output_path:
            await output_handler(bot=bot, update=message, output_path=output_path, input_path=video_path, sent_message=sent_message)
        else:
            await sent_message.edit_text("❌ Trimming failed.")
            if video_path and os.path.exists(video_path): os.remove(video_path)
    except Exception as e:
        LOGGER.error(f"Error in handle_trim_task: {e}")
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
