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
  LOG_CHANNEL,
  UPDATES_CHANNEL,
  SESSION_NAME,
  data,
  app  
)
from bot.config import Config
from bot.helper_funcs.ffmpeg import (
  convert_video,
  convert_video1,  # Add this line
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
    
async def incoming_compress_message_f(update):
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
    
    chat_id = LOG_CHANNEL
    utc_now = datetime.datetime.utcnow()
    ist_now = utc_now + datetime.timedelta(minutes=30, hours=5)
    ist = ist_now.strftime("%d/%m/%Y, %H:%M:%S")
    bst_now = utc_now + datetime.timedelta(minutes=00, hours=6)
    bst = bst_now.strftime("%d/%m/%Y, %H:%M:%S")
    now = f"\n{ist} (GMT+05:30)`\n`{bst} (GMT+06:00)"
    download_start = await bot.send_message(chat_id, f"<blockquote>**𝙱𝚘𝚝 𝙱𝚎𝚌𝚘𝚖𝚎 𝙱𝚞𝚜𝚢 𝙽𝚘𝚠...⛈**</blockquote>")
    
    try:
        d_start = time.time()
        status = DOWNLOAD_LOCATION + "/status.json"
        with open(status, 'w') as f:
            statusMsg = {
                'running': True,
                'message': sent_message.id
            }
            json.dump(statusMsg, f, indent=2)
            
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
        LOGGER.info(saved_file_path)  
        LOGGER.info(video)
        
        if video is None:
            try:
                await sent_message.edit_text(text="Dᴏᴡɴʟᴏᴀᴅ Sᴛᴏᴘᴘᴇᴅ 🛑")
                await bot.send_message(chat_id, f"<blockquote>**𝙵𝚒𝚕𝚎 𝙳𝚘𝚠𝚗𝚕𝚘𝚊𝚍 𝚂𝚝𝚘𝚙𝚙𝚎𝚍.\n...𝙱𝚘𝚝 𝚒𝚜 𝙵𝚛𝚎𝚎 𝙽𝚘𝚠...🍃**</blockquote>")
                await download_start.delete()
            except:
                pass
            LOGGER.info("Dᴏᴡɴʟᴏᴀᴅ Sᴛᴏᴘᴘᴇᴅ 🛑")
            return
            
    except ValueError as e:
        try:
            await sent_message.edit_text(text=str(e))
        except:
            pass
        return
            
    try:
        await sent_message.edit_text(text=Localisation.SAVED_RECVD_DOC_FILE)
    except:
        pass     
    
    if os.path.exists(saved_file_path):
        downloaded_time = TimeFormatter((time.time() - d_start)*1000)
        
        duration, bitrate = await get_video_duration_and_bitrate(saved_file_path)
        
        if duration <= 0:
            try:
                await sent_message.edit_text(text="⚠️ Gᴇᴛᴛɪɴɢ Vɪᴅᴇᴏ Mᴇᴛᴀ Dᴀᴛᴀ Fᴀɪʟᴇᴅ ⚠️")
                await bot.send_message(chat_id, f"<blockquote>**𝙵𝚒𝚕𝚎 𝙳𝚘𝚠𝚗𝚕𝚘𝚊𝚍 𝙵𝚊𝚒𝚕𝚎𝚍.\n...𝙱𝚘𝚝 𝚒𝚜 𝙵𝚛𝚎𝚎 𝙽𝚘𝚠...🍃**</blockquote>")
                await download_start.delete()
            except:
                pass                    
            return
            
        screenshot_time = duration / 2 if duration > 0 else 60
        
        custom_thumb = os.path.join("thumbnails", f"{update.from_user.id}.jpg")
        if os.path.exists(custom_thumb):
            thumb_image_path = custom_thumb
            is_custom_thumb = True
        else:
            thumb_image_path = os.path.join(DOWNLOAD_LOCATION, f"thumb_{int(time.time())}.jpg")
            thumb_image_path = get_thumbnail(
                saved_file_path,
                thumb_image_path,
                time_offset=str(screenshot_time)
            )
            is_custom_thumb = False
        
        await download_start.delete()
        compress_start = await bot.send_message(chat_id, f"<blockquote>**𝙴𝚗𝚌𝚘𝚍𝚒𝚗𝚐 𝚅𝚒𝚍𝚎𝚘...⚙**</blockquote>")
        await sent_message.edit_text(text=Localisation.COMPRESS_START)
        
        c_start = time.time()

        user_id = update.from_user.id
        watermark_url = await db.get_watermark_url(user_id)

        if watermark_url:
            o = await convert_video1(
                video,
                DOWNLOAD_LOCATION,
                duration,
                bot,
                sent_message,
                compress_start,
                watermark_url=watermark_url,
                user_id=user_id
            )
        else:
            o = await convert_video1(
                video,
                DOWNLOAD_LOCATION,
                duration,
                bot,
                sent_message,
                compress_start,
                user_id=user_id
            )
        
        compressed_time = TimeFormatter((time.time() - c_start)*1000)
        LOGGER.info(o)
        
        if o == 'stopped':
            return
            
        if o is not None:
            await compress_start.delete()
            upload_start = await bot.send_message(chat_id, f"<blockquote>**𝚄𝚙𝚕𝚘𝚊𝚍𝚒𝚗𝚐 𝚅𝚒𝚍𝚎𝚘 𝚘𝚗 𝚃𝙶...📥**</blockquote>")
            await sent_message.edit_text(text=Localisation.UPLOAD_START)
            
            u_start = time.time()
            caption = Localisation.COMPRESS_SUCCESS.replace('{}', downloaded_time, 1).replace('{}', compressed_time, 1)
            
            upload = await bot.send_document(
                chat_id=update.chat.id,
                document=o,
                caption=caption,
                force_document=True,
                thumb=thumb_image_path,
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
                from bot.helper_funcs.utils import copy_to_dump_channel
                await copy_to_dump_channel(bot, upload, update.from_user.id if update.from_user else "Unknown")

            if upload is None:
                try:
                    await sent_message.edit_text(text="Uᴘʟᴏᴀᴅ Sᴛᴏᴘᴘᴇᴅ 🛑")
                    await bot.send_message(chat_id, f"<blockquote>**𝙵𝚒𝚕𝚎 𝚄𝚙𝚕𝚘𝚊𝚍 𝚜𝚝𝚘𝚙𝚙𝚎𝚍.\n...𝙱𝚘𝚝 𝚒𝚜 𝙵𝚛𝚎𝚎 𝙽𝚘𝚠...🍃**</blockquote>")
                    await upload_start.delete()
                except:
                    pass
                return
                
            uploaded_time = TimeFormatter((time.time() - u_start)*1000)
            await sent_message.delete()
            await upload_start.delete()
            await bot.send_message(chat_id, f"<blockquote>**𝙴𝙽𝙲𝙾𝙳𝙴𝙳 𝚄𝚙𝚕𝚘𝚊𝚍 𝙳𝚘𝚗𝚎.\n...𝙱𝚘𝚝 𝚒𝚜 𝙵𝚛𝚎𝚎 𝙽𝚘𝚠...🍃**</blockquote>")
            
            LOGGER.info(upload.caption)
            try:
                await upload.edit_caption(caption=upload.caption.replace('{}', uploaded_time))
            except:
                pass

            # Cleanup
            if not is_custom_thumb and thumb_image_path and os.path.exists(thumb_image_path):
                os.remove(thumb_image_path)
            if o and os.path.exists(o):
                os.remove(o)
            if saved_file_path and os.path.exists(saved_file_path):
                os.remove(saved_file_path)
        else:
            try:
                await sent_message.edit_text(text="⚠️ Cᴏᴍᴘʀᴇꜱꜱɪᴏɴ Fᴀɪʟᴇᴅ ⚠️")
                await bot.send_message(chat_id, f"<blockquote>**𝚅𝚒𝚍𝚎𝚘 𝙲𝚘𝚖𝚙𝚛𝚎𝚜𝚜𝚒𝚘𝚗 𝚏𝚊𝚒𝚕𝚎𝚍.\n...𝙱𝚘𝚝 𝚒𝚜 𝙵𝚛𝚎𝚎 𝙽𝚘𝚠...🍃</blockquote>")
                await download_start.delete()
            except:
                pass
                
    else:
        try:
            await sent_message.edit_text(text="⚠️ Fᴀɪʟᴇᴅ Dᴏᴡɴʟᴏᴀᴅᴇᴅ Pᴀᴛʜ ɴᴏᴛ Exɪꜱᴛ ⚠️")
            await bot.send_message(chat_id, f"<blockquote>**𝙵𝚒𝚕𝚎 𝙳𝚘𝚠𝚗𝚕𝚘𝚊𝚍𝚎𝚍 𝙴𝚛𝚛𝚘𝚛!\n...𝙱𝚘𝚝 𝚒𝚜 𝙵𝚛𝚎𝚎 𝙽𝚘𝚠...🍃**</blockquote>")
            await download_start.delete()
        except:
            pass
    
async def incoming_cancel_message_f(bot, update):
    if update.from_user.id not in AUTH_USERS:      
        try:
            await update.message.delete()
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
