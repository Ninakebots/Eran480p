# Developer: @TheAlphaBotz
# Organization: Anime Junctions
# © 2025 All Rights Reserved

import os
import time
import logging
import json
import aiohttp
import shutil
from bot import data, AUTH_USERS, AUTH_CHATS, DUMP_CHANNEL, GOFILE_TOKEN, DOWNLOAD_LOCATION
from bot.helper_funcs.database import db, get_user_data
from bot.localisation import Localisation
from bot.helper_funcs.display_progress import progress_for_pyrogram, TimeFormatter
from bot.helper_funcs.gofile import upload_gofile

LOGGER = logging.getLogger(__name__)

# Character mapping for Mathematical Sans-Serif used by style_text (imported from utils)
def style_text(text):
    from bot.helper_funcs.utils import style_text as utils_style_text
    return utils_style_text(text)

def hbs(size):
    from bot.helper_funcs.utils import hbs as utils_hbs
    return utils_hbs(size)

async def copy_to_dump_channel(bot, message, user_id):
    if not DUMP_CHANNEL:
        return
    try:
        # Handle conversion of DUMP_CHANNEL to int if it's a numeric string
        # Pyrogram requires channel IDs to be integers starting with -100
        dump_chat = DUMP_CHANNEL
        if isinstance(dump_chat, str):
            if dump_chat.startswith("-100") or dump_chat.isdigit() or (dump_chat.startswith("-") and dump_chat[1:].isdigit()):
                try:
                    dump_chat = int(dump_chat)
                except ValueError:
                    pass

        caption = f"**User ID:** `{user_id}`\n\n{message.caption or ''}"

        # Using copy is more robust as it handles all media types and metadata
        await message.copy(
            chat_id=dump_chat,
            caption=caption
        )
    except Exception as e:
        LOGGER.error(f"Error copying to dump channel: {e}")

async def output_handler(bot, update, output_path, download_time=None, encoding_time=None, thumb_path=None, input_path=None, sent_message=None, task_type=None):
    user_id = update.from_user.id if update.from_user else update.chat.id
    user_settings = await get_user_data(user_id)
    upload_dest = user_settings.get("upload_destination", "chat")
    upload_as = user_settings.get("upload_as", "video")

    # Override thumb_path with user's custom thumbnail if available
    custom_thumb = await db.get_thumbnail(user_id)
    if custom_thumb:
        thumb_path = custom_thumb

    # Determine destination chat
    dest_chat = update.chat.id
    if upload_dest == "pm":
        dest_chat = user_id
    elif isinstance(upload_dest, int):
        dest_chat = upload_dest

    u_start = time.time()
    if not sent_message:
        sent_message = await bot.send_message(chat_id=update.chat.id, text=Localisation.UPLOAD_START, reply_to_message_id=update.id)
    else:
        try:
            await sent_message.edit_text(text=Localisation.UPLOAD_START)
        except:
            pass

    try:
        # Generate initial caption
        d_time = download_time or "N/A"
        e_time = encoding_time or "N/A"
        file_name = os.path.basename(output_path)
        file_size = hbs(os.path.getsize(output_path))

        custom_caption = await db.get_custom_caption(user_id)
        if custom_caption:
            caption = custom_caption.replace("{file_name}", file_name).replace("{file_size}", file_size).replace("{download_time}", d_time).replace("{encoding_time}", e_time)
        else:
            if task_type == "rename":
                caption = f"✅ **{style_text('File Renamed Successfully!')}**\n\n📁 **{style_text('Name:')}** `{file_name}`\n⚖️ **{style_text('Size:')}** `{file_size}`"
            elif task_type == "extract_audio":
                caption = f"🎧 **{style_text('Audio Extracted Successfully!')}**\n\n📁 **{style_text('Name:')}** `{file_name}`\n⚖️ **{style_text('Size:')}** `{file_size}`"
            elif task_type == "extract_sub":
                caption = f"📝 **{style_text('Subtitles Extracted Successfully!')}**\n\n📁 **{style_text('Name:')}** `{file_name}`\n⚖️ **{style_text('Size:')}** `{file_size}`"
            elif task_type == "zip":
                caption = f"🗜️ **{style_text('File Zipped Successfully!')}**\n\n📁 **{style_text('Name:')}** `{file_name}`\n⚖️ **{style_text('Size:')}** `{file_size}`"
            else:
                from bot.helper_funcs.ffmpeg import get_encoding_settings
                s = await get_encoding_settings(user_settings)

                caption = (
                    f"✨ **{style_text('Video Encoded Successfully!')}** ✨\n\n"
                    f"📁 **{style_text('Name:')}** `{file_name}`\n"
                    f"⚖️ **{style_text('Size:')}** `{file_size}`\n\n"
                    f"<blockquote>"
                    f"<b>🎥 {style_text('Codec:')}</b> {s['codec']} ({s['bits']})\n"
                    f"<b>📊 {style_text('CRF:')}</b> {s['crf']} | <b>⚡ {style_text('Preset:')}</b> {s['preset']}\n"
                    f"<b>📥 {style_text('Download Time:')}</b> {d_time}\n"
                    f"<b>📀 {style_text('Encoding Time:')}</b> {e_time}\n"
                    f"<b>📤 {style_text('Upload Time:')}</b> {{}}"
                    f"</blockquote>\n\n"
                    f"<b>{style_text('Powered By @Team_Wine')}</b>"
                )

        # Upload
        upload = None
        if upload_dest == "gofile":
            try:
                await sent_message.edit_text(f"📤 **{style_text('Uploading to Gofile.io...')}**")
                download_url = await upload_gofile(output_path, token=GOFILE_TOKEN)
                if download_url:
                    u_time = TimeFormatter((time.time() - u_start) * 1000)

                    if custom_caption:
                        text = caption.replace("{upload_time}", u_time) + f"\n\n🔗 **Download Link:** {download_url}"
                    else:
                        if "{}" in caption:
                             text = caption.replace("{}", u_time, 1) + f"\n\n🔗 **Download Link:** {download_url}"
                        else:
                             text = caption + f"\n\n🔗 **{style_text('Download Link:')}** {download_url}"

                    await bot.send_message(
                        chat_id=update.chat.id,
                        text=text,
                        reply_to_message_id=update.id,
                        disable_web_page_preview=True
                    )
                else:
                    raise Exception("Gofile upload failed.")
            except Exception as e:
                LOGGER.error(f"Gofile upload error: {e}")
                upload_dest = "telegram" # Fallback to telegram
                await sent_message.edit_text("⚠️ Gofile upload failed. Falling back to Telegram...")

        if upload_dest != "gofile":
            ext = output_path.split('.')[-1].lower()
            common_args = {
                'chat_id': dest_chat,
                'caption': caption.replace('{}', "Calculating...", 1),
                'reply_to_message_id': update.id if dest_chat == update.chat.id else None,
                'progress': progress_for_pyrogram,
                'progress_args': (bot, Localisation.UPLOAD_START, sent_message, u_start)
            }

            if upload_as == "video" and ext in ['mp4', 'mkv', 'webm']:
                upload = await bot.send_video(
                    video=output_path,
                    thumb=thumb_path if thumb_path and os.path.exists(thumb_path) else None,
                    supports_streaming=True,
                    **common_args
                )
            elif ext in ['mp3', 'm4a', 'ogg', 'opus']:
                upload = await bot.send_audio(
                    audio=output_path,
                    thumb=thumb_path if thumb_path and os.path.exists(thumb_path) else None,
                    **common_args
                )
            else:
                upload = await bot.send_document(
                    document=output_path,
                    thumb=thumb_path if thumb_path and os.path.exists(thumb_path) else None,
                    force_document=True,
                    **common_args
                )

            u_time = TimeFormatter((time.time() - u_start) * 1000)

            if upload:
                # Update caption with actual upload time
                try:
                    if custom_caption:
                        final_caption = caption.replace("{upload_time}", u_time)
                    else:
                        final_caption = caption.replace('{}', u_time, 1)
                    await upload.edit_caption(caption=final_caption)
                except Exception as e:
                    LOGGER.error(f"Error editing caption: {e}")

                # Copy to dump channel
                await copy_to_dump_channel(bot, upload, update.from_user.id if update.from_user else "Unknown")

        try:
            if sent_message:
                await sent_message.delete()
        except:
            pass

    except Exception as e:
        LOGGER.error(f"Upload error: {e}")
        try:
            await sent_message.edit_text(f"❌ Upload failed: {str(e)[:100]}")
        except:
            pass
    finally:
        # Centralized cleanup
        uid = update.from_user.id if update.from_user else "default"
        custom_thumb = os.path.join("thumbnails", f"{uid}.jpg")

        for p in [output_path, thumb_path, input_path]:
            if p and os.path.exists(p):
                # Don't delete the custom thumbnail
                if os.path.abspath(p) == os.path.abspath(custom_thumb):
                    continue
                try:
                    if os.path.isfile(p): os.remove(p)
                    elif os.path.isdir(p): shutil.rmtree(p)
                except Exception as e:
                    LOGGER.warning(f"Failed to cleanup {p}: {e}")

TELEGRAPH_TOKEN = None

async def upload_to_telegraph(title, content):
    global TELEGRAPH_TOKEN
    try:
        async with aiohttp.ClientSession() as session:
            if not TELEGRAPH_TOKEN:
                # Create account anonymously
                async with session.get("https://api.telegra.ph/createAccount", params={
                    "short_name": "EncoderBot",
                    "author_name": "ZaniEncoder"
                }) as resp:
                    acc_data = await resp.json()
                    if not acc_data.get("ok"):
                        return None
                    TELEGRAPH_TOKEN = acc_data["result"]["access_token"]

            # Content must be a list of nodes. We'll wrap our text in <pre>
            formatted_content = [{"tag": "pre", "children": [content]}]

            async with session.post("https://api.telegra.ph/createPage", data={
                "access_token": TELEGRAPH_TOKEN,
                "title": title,
                "author_name": "ZaniEncoder",
                "content": json.dumps(formatted_content),
                "return_content": "false"
            }) as resp:
                page_data = await resp.json()
                if page_data.get("ok"):
                    return page_data["result"]["url"]
                else:
                    LOGGER.error(f"Telegraph error: {page_data}")
                    # If token is invalid, clear it so it's recreated next time
                    if "ACCESS_TOKEN_INVALID" in str(page_data):
                        TELEGRAPH_TOKEN = None
                    return None
    except Exception as e:
        LOGGER.error(f"Error uploading to Telegraph: {e}")
        return None
