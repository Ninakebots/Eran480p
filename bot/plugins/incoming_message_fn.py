import datetime
import logging
import re
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)
LOGGER = logging.getLogger(__name__)
import os, time, asyncio, json
from bot.localisation import Localisation
from bot import (
  DOWNLOAD_LOCATION, 
  AUTH_USERS,
  UPDATES_CHANNEL,
  SESSION_NAME,
  data,
  app,
  BOT_USERNAME
)
from bot.config import Config
from bot.helper_funcs.ffmpeg import (
  media_info,
  take_screen_shot,
  get_duration,
  get_thumbnail
)
from bot.helper_funcs.display_progress import (
  progress_for_pyrogram,
  TimeFormatter,
  humanbytes
)
from bot.helper_funcs.utils import safe_float_convert, safe_int_convert

from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.types import ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant, UsernameNotOccupied, ChatAdminRequired, PeerIdInvalid


CURRENT_PROCESSES = {}
CHAT_FLOOD = {}
broadcast_ids = {}
bot = app        

async def get_video_duration_and_bitrate(file_path):
    try:
        media_data = await media_info(file_path)
        duration = 0
        bitrate = 0
        
        if media_data and isinstance(media_data, dict):
            if 'streams' in media_data:
                for stream in media_data['streams']:
                    if stream.get('codec_type') == 'video':
                        duration = safe_float_convert(stream.get('duration'), 0)
                        bitrate = safe_int_convert(stream.get('bit_rate'), 0)
                        break
            
            if duration == 0 and 'format' in media_data:
                duration = safe_float_convert(media_data['format'].get('duration'), 0)

            if bitrate == 0 and 'format' in media_data:
                bitrate = safe_int_convert(media_data['format'].get('bit_rate'), 0)
        
        if duration == 0:
            duration = get_duration(file_path)
            
        return duration, bitrate
    except Exception as e:
        LOGGER.error(f"Error getting video info: {e}")
        try:
            duration = get_duration(file_path)
            return duration, 0
        except:
            return 0, 0

@app.on_message(filters.command(["start", f"start@{BOT_USERNAME}"]))
async def incoming_start_message_f(bot, update):
    mention = update.from_user.mention if update.from_user else "User"
    start_text = Localisation.START_TEXT.format(mention=mention)

    if Config.START_PIC:
        await bot.send_photo(
            chat_id=update.chat.id,
            photo=Config.START_PIC,
            caption=start_text,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton('𝖳𝖾𝖺𝗆 𝖶𝗂𝗇𝖾', url='https://t.me/Team_Wine')
                    ],
                    [
                        InlineKeyboardButton(Localisation.HELP_BUTTON, callback_data="help"),
                        InlineKeyboardButton(Localisation.ABOUT_BUTTON, callback_data="about")
                    ]
                ]
            ),
            reply_to_message_id=update.id,
        )
    else:
        await bot.send_message(
            chat_id=update.chat.id,
            text=start_text,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton('𝖳𝖾𝖺𝗆 𝖶𝗂𝗇𝖾', url='https://t.me/Team_Wine')
                    ],
                    [
                        InlineKeyboardButton(Localisation.HELP_BUTTON, callback_data="help"),
                        InlineKeyboardButton(Localisation.ABOUT_BUTTON, callback_data="about")
                    ]
                ]
            ),
            reply_to_message_id=update.id,
        )
    
async def incoming_compress_message_f(update, user_settings=None):
    isAuto = True
    d_start = time.time()
    c_start = time.time()
    u_start = time.time()
    
    sent_message = await bot.send_message(
        chat_id=update.chat.id,
        text=Localisation.DOWNLOAD_START,
        reply_to_message_id=update.id
    )
    
    status = os.path.join(DOWNLOAD_LOCATION, f"status_{sent_message.id}.json")
    try:
        d_start = time.time()
        os.makedirs(DOWNLOAD_LOCATION, exist_ok=True)
        
        # Save status
        user_id = update.from_user.id if update.from_user else update.chat.id
        with open(status, 'w') as f:
            statusMsg = {
                'running': True,
                'message': sent_message.id,
                'user_id': user_id
            }
            json.dump(statusMsg, f, indent=2)
        
        # Download media    
        try:
            video = await bot.download_media(
                message=update,
                progress=progress_for_pyrogram,
                progress_args=(
                    bot,
                    Localisation.DOWNLOAD_START,
                    sent_message,
                    d_start
                )
            )
        except Exception as de:
            LOGGER.error(f"bot.download_media failed: {de}")
            try:
                await sent_message.edit_text(text=f"⚠️ Dᴏᴡɴʟᴏᴀᴅ Eʀʀᴏʀ: {str(de)[:100]}")
            except:
                pass
            return
        
        saved_file_path = video
        if video:
            LOGGER.info(f"Downloaded video path: {video}")
        else:
            LOGGER.error("Download failed or was cancelled, video path is None")
            try:
                await sent_message.edit_text(text="Dᴏᴡɴʟᴏᴀᴅ Fᴀɪʟᴇᴅ 🛑")
            except:
                pass
            return
            
    except Exception as e:
        LOGGER.error(f"General Download error: {str(e)}")
        try:
            await sent_message.edit_text(text=f"Download error: {str(e)[:100]}")
        except:
            pass
        return
            
    try:
        await sent_message.edit_text(text=Localisation.SAVED_RECVD_DOC_FILE)
    except:
        pass     
    
    if os.path.exists(saved_file_path):
        downloaded_time = TimeFormatter((time.time() - d_start)*1000)
        
        # Get video info
        duration, bitrate = await get_video_duration_and_bitrate(saved_file_path)
        LOGGER.info(f"Video duration: {duration}, bitrate: {bitrate}")
        
        if duration <= 0:
            LOGGER.error(f"Invalid video duration: {duration}")
            try:
                await sent_message.edit_text(text="⚠️ Gᴇᴛᴛɪɴɢ Vɪᴅᴇᴏ Mᴇᴛᴀ Dᴀᴛᴀ Fᴀɪʟᴇᴅ ⚠️")
            except:
                pass                    
            return
            
        # Generate thumbnail
        screenshot_time = duration / 2 if duration > 0 else 60
        
        user_id = update.from_user.id if update.from_user else update.chat.id
        custom_thumb = os.path.join("thumbnails", f"{user_id}.jpg")
        if os.path.exists(custom_thumb):
            thumb_image_path = custom_thumb
            is_custom_thumb = True
            LOGGER.info("Using custom thumbnail")
        else:
            thumb_image_path = os.path.join(DOWNLOAD_LOCATION, f"thumb_{int(time.time())}.jpg")
            try:
                thumb_image_path = get_thumbnail(
                    saved_file_path,
                    thumb_image_path,
                    time_offset=str(screenshot_time)
                )
                is_custom_thumb = False
                LOGGER.info(f"Generated thumbnail: {thumb_image_path}")
            except Exception as e:
                LOGGER.error(f"Thumbnail generation failed: {e}")
                thumb_image_path = None
                is_custom_thumb = False
        
        # Start compression
        try:
            await sent_message.edit_text(text=Localisation.COMPRESS_START)
        except:
            pass
        
        c_start = time.time()

        try:
            # Get user settings from DB if not provided
            if user_settings is None:
                user_id = update.from_user.id if (update.from_user and update.from_user.id) else update.chat.id
                from bot.helper_funcs.database import get_user_data
                user_settings = await get_user_data(user_id)

            # Compress video
            from bot.helper_funcs.converter import convert_video_robust
            o = await convert_video_robust(
                saved_file_path,  # Use saved_file_path instead of video
                DOWNLOAD_LOCATION,
                duration,
                bot,
                sent_message,
                user_settings
            )
            
            LOGGER.info(f"convert_video_robust returned: {o}")
            
        except Exception as e:
            LOGGER.error(f"Compression error: {str(e)}")
            LOGGER.exception("Full traceback:")
            try:
                await sent_message.edit_text(text=f"⚠️ Compression error: {str(e)[:100]} ⚠️")
            except:
                pass
            return
        
        compressed_time = TimeFormatter((time.time() - c_start)*1000)
        
        if o == 'stopped':
            LOGGER.info("Compression stopped by user")
            try:
                await sent_message.edit_text(text="Compression stopped by user")
            except:
                pass
            return
            
        if o and os.path.exists(o):
            # Use centralized output_handler
            from bot.helper_funcs.output import output_handler
            await output_handler(
                bot=bot,
                update=update,
                output_path=o,
                download_time=downloaded_time,
                encoding_time=compressed_time,
                thumb_path=thumb_image_path,
                input_path=saved_file_path,
                sent_message=sent_message
            )
        else:
            LOGGER.error(f"Compression failed - output path is None or doesn't exist: {o}")
            error_msg = "⚠️ Cᴏᴍᴘʀᴇꜱꜱɪᴏɴ Fᴀɪʟᴇᴅ ⚠️"
            if o is None:
                error_msg += "\n(FFmpeg failed to produce output)"
            elif not os.path.exists(o):
                error_msg += f"\n(Output file not found: {os.path.basename(o)})"

            try:
                await sent_message.edit_text(text=error_msg)
            except:
                pass
    else:
        LOGGER.error(f"Downloaded file doesn't exist: {saved_file_path}")
        try:
            await sent_message.edit_text(text="⚠️ Fᴀɪʟᴇᴅ Dᴏᴡɴʟᴏᴀᴅᴇᴅ Pᴀᴛʜ ɴᴏᴛ Exɪꜱᴛ ⚠️")
        except:
            pass
    
    # Clean up status file
    try:
        if os.path.exists(status):
            os.remove(status)
    except:
        pass

async def incoming_cancel_message_f(bot, update):
    user_id = update.from_user.id if update.from_user else None
    if user_id not in AUTH_USERS:
        # Check if user has an active task in DOWNLOAD_LOCATION
        has_task = False
        for f in os.listdir(DOWNLOAD_LOCATION):
            if f.startswith("status_") and f.endswith(".json"):
                try:
                    with open(os.path.join(DOWNLOAD_LOCATION, f), 'r') as status_file:
                        data = json.load(status_file)
                        if data.get('user_id') == user_id:
                            has_task = True
                            break
                except:
                    pass

        if not has_task:
            try:
                await update.delete()
            except:
                pass
            return

    # Find tasks for this user (or all if admin)
    tasks = []
    for f in os.listdir(DOWNLOAD_LOCATION):
        if f.startswith("status_") and f.endswith(".json"):
            try:
                with open(os.path.join(DOWNLOAD_LOCATION, f), 'r') as status_file:
                    data = json.load(status_file)
                    if user_id in AUTH_USERS or data.get('user_id') == user_id:
                        tasks.append(f)
            except:
                pass

    if tasks:
        inline_keyboard = []
        ikeyboard = []
        ikeyboard.append(InlineKeyboardButton("Yᴇꜱ 🚫", callback_data=("fuckingdo").encode("UTF-8")))
        ikeyboard.append(InlineKeyboardButton("Nᴏ 🤗", callback_data=("fuckoff").encode("UTF-8")))
        inline_keyboard.append(ikeyboard)
        reply_markup = InlineKeyboardMarkup(inline_keyboard)
        await update.reply_text("Aʀᴇ Yᴏᴜ Sᴜʀᴇ? 🚫 Tʜɪꜱ ᴡɪʟʟ Sᴛᴏᴘ ᴛʜᴇ Cᴏᴍᴘʀᴇꜱꜱɪᴏɴ!", reply_markup=reply_markup, quote=True)
    else:
        await bot.send_message(
            chat_id=update.chat.id,
            text="<blockquote>No active compression exists</blockquote>",
            reply_to_message_id=update.id
                )
