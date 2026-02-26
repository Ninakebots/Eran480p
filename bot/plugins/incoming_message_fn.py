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
  app  
)
from bot.config import Config
from bot.helper_funcs.ffmpeg import (
  convert_video,
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

from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.types import ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant, UsernameNotOccupied, ChatAdminRequired, PeerIdInvalid


CURRENT_PROCESSES = {}
CHAT_FLOOD = {}
broadcast_ids = {}
bot = app        

def safe_float_convert(value, default=0.0):
    try:
        if isinstance(value, (int, float)):
            return float(value)
        elif isinstance(value, str):
            cleaned = re.sub(r'[^\d.]', '', str(value))
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
            cleaned = re.sub(r'[^\d]', '', str(value))
            return int(cleaned) if cleaned else default
        return default
    except (ValueError, TypeError):
        return default

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

async def incoming_start_message_f(bot, update):
    if Config.START_PIC:
        await bot.send_photo(
            chat_id=update.chat.id,
            photo=Config.START_PIC,
            caption=Localisation.START_TEXT,
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
            text=Localisation.START_TEXT,
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
    if not update.from_user:
        return
    isAuto = True
    d_start = time.time()
    c_start = time.time()
    u_start = time.time()
    status = DOWNLOAD_LOCATION + "/status.json"
    
    sent_message = await bot.send_message(
        chat_id=update.chat.id,
        text=Localisation.DOWNLOAD_START,
        reply_to_message_id=update.id
    )
    
    download_start = None
    
    try:
        d_start = time.time()
        os.makedirs(DOWNLOAD_LOCATION, exist_ok=True)
        
        # Save status
        with open(status, 'w') as f:
            statusMsg = {
                'running': True,
                'message': sent_message.id
            }
            json.dump(statusMsg, f, indent=2)
        
        # Download media    
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
        
        saved_file_path = video
        if video:
            LOGGER.info(f"Downloaded video path: {video}")
        else:
            LOGGER.error("Download failed or was cancelled, video path is None")
            try:
                await sent_message.edit_text(text="Dᴏᴡɴʟᴏᴀᴅ Fᴀɪʟᴇᴅ 🛑")
                if download_start: await download_start.delete()
            except:
                pass
            return
            
    except Exception as e:
        LOGGER.error(f"Download error: {str(e)}")
        try:
            await sent_message.edit_text(text=f"Download error: {str(e)[:100]}")
            if download_start: await download_start.delete()
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
                if download_start: await download_start.delete()
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
        
        # Clean up download start message
        try:
            if download_start: await download_start.delete()
        except:
            pass
            
        # Start compression
        compress_start = None
        await sent_message.edit_text(text=Localisation.COMPRESS_START)
        
        c_start = time.time()

        try:
            # Get user settings from DB if not provided
            if user_settings is None:
                user_id = update.from_user.id if update.from_user else update.chat.id
                from bot.helper_funcs.database import get_user_data
                user_settings = await get_user_data(user_id)

            # Compress video
            o = await convert_video(
                saved_file_path,  # Use saved_file_path instead of video
                DOWNLOAD_LOCATION,
                duration,
                bot,
                sent_message,
                user_settings
            )
            
            LOGGER.info(f"convert_video returned: {o}")
            
        except Exception as e:
            LOGGER.error(f"Compression error: {str(e)}")
            LOGGER.exception("Full traceback:")
            try:
                await sent_message.edit_text(text=f"⚠️ Compression error: {str(e)[:100]} ⚠️")
            except:
                pass
            finally:
                try:
                    if compress_start: await compress_start.delete()
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
            # Get file size for logging
            file_size = os.path.getsize(o)
            LOGGER.info(f"Compression successful: {o} (size: {humanbytes(file_size)})")
            
            # Clean up compression message
            try:
                if compress_start: await compress_start.delete()
            except:
                pass
                
            # Start upload
            upload_start = None
            await sent_message.edit_text(text=Localisation.UPLOAD_START)
            
            u_start = time.time()
            caption = Localisation.COMPRESS_SUCCESS.replace('{}', downloaded_time, 1).replace('{}', compressed_time, 1)
            
            try:
                # Upload document
                upload = await bot.send_document(
                    chat_id=update.chat.id,
                    document=o,
                    caption=caption,
                    force_document=True,
                    thumb=thumb_image_path if thumb_image_path and os.path.exists(thumb_image_path) else None,
                    reply_to_message_id=update.id,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        bot,
                        Localisation.UPLOAD_START,
                        sent_message,
                        u_start
                    )
                )
                
                if upload:
                    LOGGER.info(f"Upload successful: {upload.id}")
                    # Copy to dump channel if configured
                    try:
                        from bot.helper_funcs.utils import copy_to_dump_channel
                        await copy_to_dump_channel(bot, upload, update.from_user.id if update.from_user else "Unknown")
                    except Exception as e:
                        LOGGER.error(f"Failed to copy to dump channel: {e}")

                uploaded_time = TimeFormatter((time.time() - u_start)*1000)
                
                # Clean up messages
                try:
                    await sent_message.delete()
                except:
                    pass
                    
                try:
                    await upload_start.delete()
                except:
                    pass
                    
                # Update caption with upload time
                if upload and upload.caption:
                    try:
                        new_caption = upload.caption.replace('{}', uploaded_time)
                        await upload.edit_caption(caption=new_caption)
                    except Exception as e:
                        LOGGER.error(f"Failed to edit caption: {e}")

            except Exception as e:
                LOGGER.error(f"Upload error: {str(e)}")
                LOGGER.exception("Upload traceback:")
                try:
                    await sent_message.edit_text(text=f"⚠️ Upload error: {str(e)[:100]} ⚠️")
                except:
                    pass
            finally:
                # Cleanup files
                try:
                    if not is_custom_thumb and thumb_image_path and os.path.exists(thumb_image_path):
                        os.remove(thumb_image_path)
                        LOGGER.info(f"Removed thumbnail: {thumb_image_path}")
                except Exception as e:
                    LOGGER.error(f"Failed to remove thumbnail: {e}")
                    
                try:
                    if o and os.path.exists(o):
                        os.remove(o)
                        LOGGER.info(f"Removed compressed file: {o}")
                except Exception as e:
                    LOGGER.error(f"Failed to remove compressed file: {e}")
                    
                try:
                    if saved_file_path and os.path.exists(saved_file_path):
                        os.remove(saved_file_path)
                        LOGGER.info(f"Removed original file: {saved_file_path}")
                except Exception as e:
                    LOGGER.error(f"Failed to remove original file: {e}")
        else:
            LOGGER.error(f"Compression failed - output path is None or doesn't exist: {o}")
            try:
                await sent_message.edit_text(text="⚠️ Cᴏᴍᴘʀᴇꜱꜱɪᴏɴ Fᴀɪʟᴇᴅ ⚠️")
            except:
                pass
            finally:
                try:
                    if compress_start: await compress_start.delete()
                except:
                    pass
    else:
        LOGGER.error(f"Downloaded file doesn't exist: {saved_file_path}")
        try:
            await sent_message.edit_text(text="⚠️ Fᴀɪʟᴇᴅ Dᴏᴡɴʟᴏᴀᴅᴇᴅ Pᴀᴛʜ ɴᴏᴛ Exɪꜱᴛ ⚠️")
        except:
            pass
        finally:
            try:
                if download_start: await download_start.delete()
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
        try:
            await update.delete()
        except:
            pass
        return

    status = DOWNLOAD_LOCATION + "/status.json"
    if os.path.exists(status):
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
