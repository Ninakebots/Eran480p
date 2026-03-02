from datetime import datetime as dt
import os
import time
import logging
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message

from bot import (
    APP_ID, API_HASH, AUTH_USERS, DOWNLOAD_LOCATION, LOGGER, TG_BOT_TOKEN, BOT_USERNAME, SESSION_NAME, data, app, AUTH_CHATS, 
    crf, resolution, audio_b, preset, codec, GOFILE_TOKEN
)
from bot.helper_funcs.utils import add_task, on_task_complete, sysinfo, is_auth, hbs
from bot.helper_funcs.display_progress import progress_for_pyrogram
from bot.helper_funcs.gofile import upload_gofile
from bot.helper_funcs.database import db, get_user_data, update_user_data
from bot.localisation import Localisation
from bot.plugins.incoming_message_fn import incoming_start_message_f, incoming_compress_message_f, incoming_cancel_message_f
from bot.plugins.status_message_fn import eval_message_f, exec_message_f, upload_log_file
from bot.plugins.subtitle_handlers import *
from bot.plugins.encoding_handlers import *
from bot.plugins.media_tools import *
from bot.plugins.utility_handlers import *
from bot.plugins.auth_handlers import *
from bot.plugins.user_settings import *
from bot.plugins.call_back_button_handler import button as admin_button_handler
from bot.commands import Command

# Configure logging to reduce MongoDB verbosity
logging.getLogger("pymongo").setLevel(logging.WARNING)
logging.getLogger("motor").setLevel(logging.WARNING)

crf.append("30")
codec.append("libx264")
resolution.append("840x480")
preset.append("veryfast")
audio_b.append("32k")

uptime = dt.now()

def ts(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = (
        ((str(days) + "d, ") if days else "") + 
        ((str(hours) + "h, ") if hours else "") + 
        ((str(minutes) + "m, ") if minutes else "") + 
        ((str(seconds) + "s, ") if seconds else "") + 
        ((str(milliseconds) + "ms, ") if milliseconds else "")
    )
    return tmp[:-2]

async def main_callback_handler(client, callback_query: CallbackQuery):
    await admin_button_handler(client, callback_query)

async def init_bot():
    try:
        await db.connect()
        LOGGER.info("Database connected successfully")
    except Exception as e:
        LOGGER.error(f"Failed to connect to database: {e}")
        LOGGER.info("Bot will continue without database features")

if __name__ == "__main__":
    if not os.path.isdir(DOWNLOAD_LOCATION):
        os.makedirs(DOWNLOAD_LOCATION)

    @app.on_message(filters.incoming & filters.command(["crf", f"crf@{BOT_USERNAME}"]))
    async def changecrf(app, message):
        if message.chat.id in AUTH_USERS:
            args = message.text.split()
            if len(args) < 2:
                return await message.reply_text("❌ Usage: `/crf 28`")
            cr = args[1]
            crf.insert(0, f"{cr}")
            await message.reply_text(f"📊 I will be using : {cr} crf")
        else:
            await message.reply_text("🔒 Admin Only")

    @app.on_message(filters.incoming & filters.command(["resolution", f"resolution@{BOT_USERNAME}"]))
    async def changer(app, message):
        if message.chat.id in AUTH_USERS:
            args = message.text.split()
            if len(args) < 2:
                return await message.reply_text("❌ Usage: `/resolution 1280x720` or `/resolution 720`")
            r = args[1]
            resolution.insert(0, f"{r}")
            await message.reply_text(f"🎬 I will be using : {r}")
        else:
            await message.reply_text("🔒 Admin Only")

    @app.on_message(filters.incoming & filters.command(["preset", f"preset@{BOT_USERNAME}"]))
    async def changepr(app, message):
        if message.chat.id in AUTH_USERS:
            args = message.text.split()
            if len(args) < 2:
                return await message.reply_text("❌ Usage: `/preset veryfast`")
            pop = args[1]
            preset.insert(0, f"{pop}")
            await message.reply_text(f"⚡ I will be using : {pop} preset")
        else:
            await message.reply_text("🔒 Admin Only")

    @app.on_message(filters.incoming & filters.command(["codec", f"codec@{BOT_USERNAME}"]))
    async def changecode(app, message):
        if message.chat.id in AUTH_USERS:
            args = message.text.split()
            if len(args) < 2:
                return await message.reply_text("❌ Usage: `/codec libx265`")
            col = args[1]
            codec.insert(0, f"{col}")
            await message.reply_text(f"🎥 I will be using : {col} codec")
        else:
            await message.reply_text("🔒 Admin Only")

    @app.on_message(filters.incoming & filters.command(["audio", f"audio@{BOT_USERNAME}"]))
    async def changea(app, message):
        if message.chat.id in AUTH_USERS:
            args = message.text.split()
            if len(args) < 2:
                return await message.reply_text("❌ Usage: `/audio 128k`")
            aud = args[1]
            audio_b.insert(0, f"{aud}")
            await message.reply_text(f"🎵 I will be using : {aud} audio")
        else:
            await message.reply_text("🔒 Admin Only")


    @app.on_message(filters.incoming & filters.command(["restart", f"restart@{BOT_USERNAME}"]))
    async def restarter(app, message):
        if message.chat.id in AUTH_USERS:
            await message.reply_text("♻️ Restarting...")
            quit(1)
        else:
            await message.reply_text("🔒 Admin Only")

    @app.on_message(filters.incoming & filters.command(["clear", f"clear@{BOT_USERNAME}"]))
    async def clear_queue(app, message):
        if message.chat.id not in AUTH_USERS:
            return await message.reply_text("🚫 Not authorized")
        data.clear()
        await message.reply_text("📚 Queue cleared successfully")

    @app.on_message(filters.incoming & filters.command([Command.GOFILE, f"{Command.GOFILE}@{BOT_USERNAME}"]) & is_auth)
    async def gofile_handler(client, message):
        sent_message = None
        file_path = None
        try:
            reply = message.reply_to_message
            if not reply or not (reply.video or reply.document or reply.audio or reply.animation):
                return await message.reply_text("❌ Reply to a file to upload it to Gofile.io.")

            sent_message = await message.reply_text("📥 **Downloading file...**", quote=True)

            try:
                start_time = time.time()
                file_path = await client.download_media(
                    message=reply,
                    progress=progress_for_pyrogram,
                    progress_args=(client, "📥 **Downloading...**", sent_message, start_time)
                )

                if not file_path:
                    if sent_message:
                        await sent_message.edit_text("❌ Download failed.")
                    return

                await sent_message.edit_text("📤 **Uploading to Gofile.io...**")

                download_url = await upload_gofile(file_path, token=GOFILE_TOKEN)

                if download_url:
                    file_name = os.path.basename(file_path)
                    file_size = hbs(os.path.getsize(file_path))
                    await sent_message.edit_text(
                        f"✅ **File uploaded successfully!**\n\n"
                        f"📁 **File Name:** `{file_name}`\n"
                        f"⚖️ **Size:** `{file_size}`\n\n"
                        f"🔗 **Download Link:** {download_url}",
                        disable_web_page_preview=True
                    )
                else:
                    await sent_message.edit_text("❌ Gofile upload failed. The service might be down or the file is too large.")

            except Exception as e:
                LOGGER.error(f"Error during gofile upload process: {e}")
                if sent_message:
                    try:
                        await sent_message.edit_text(f"❌ An error occurred during processing: `{e}`")
                    except:
                        pass
                else:
                    await message.reply_text(f"❌ An error occurred: `{e}`")
        except Exception as e:
            LOGGER.error(f"Top level error in gofile_handler: {e}")
            try:
                await message.reply_text(f"❌ Unexpected error: `{e}`")
            except:
                pass
        finally:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass

    @app.on_message(filters.command([Command.SETUPLOAD, f"{Command.SETUPLOAD}@{BOT_USERNAME}"]) & is_auth)
    async def setupload_command_handler(client: Client, message: Message):
        user_id = message.from_user.id
        user_data = await get_user_data(user_id)
        current_dest = user_data.get("upload_destination", "Telegram")

        text = f"📤 **Upload Settings**\n\nCᴜʀʀᴇɴᴛ Dᴇꜱᴛɪɴᴀᴛɪᴏɴ: `{current_dest.capitalize()}`\n\nSᴇʟᴇᴄᴛ ᴡʜᴇʀᴇ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴜᴘʟᴏᴀᴅ ʏᴏᴜʀ ꜰɪʟᴇꜱ:"

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Telegram", callback_data="set_upload_tg"),
                InlineKeyboardButton("Gofile", callback_data="set_upload_gofile")
            ],
            [InlineKeyboardButton("❌ Close", callback_data="close_menu")]
        ])

        await message.reply_text(text, reply_markup=keyboard)

    @app.on_callback_query(filters.regex(r"^set_upload_(tg|gofile)$"))
    async def set_upload_callback_handler(client: Client, callback_query: CallbackQuery):
        user_id = callback_query.from_user.id
        data = callback_query.data

        dest = "telegram" if data == "set_upload_tg" else "gofile"

        await update_user_data(user_id, {"upload_destination": dest})

        await callback_query.answer(f"✅ Upload destination set to {dest.capitalize()}", show_alert=True)

        # Update the message
        text = f"📤 **Upload Settings**\n\nCᴜʀʀᴇɴᴛ Dᴇꜱᴛɪɴᴀᴛɪᴏɴ: `{dest.capitalize()}`\n\nSᴇʟᴇᴄᴛ ᴡʜᴇʀᴇ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴜᴘʟᴏᴀᴅ ʏᴏᴜʀ ꜰɪʟᴇꜱ:"
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Telegram", callback_data="set_upload_tg"),
                InlineKeyboardButton("Gofile", callback_data="set_upload_gofile")
            ],
            [InlineKeyboardButton("❌ Close", callback_data="close_menu")]
        ])

        try:
            await callback_query.message.edit_text(text, reply_markup=keyboard)
        except Exception:
            pass


    @app.on_message(filters.incoming & filters.command(["settings", f"settings@{BOT_USERNAME}"]) & is_auth)
    async def settings(app, message):
        user_id = message.from_user.id if message.from_user else message.chat.id
        user_data = await get_user_data(user_id)
        up_dest = user_data.get("upload_destination", "telegram")
        await message.reply_text(f"⚙️ Current Settings:\n\n➥ Codec: {codec[0]} \n➥ Crf: {crf[0]} \n➥ Resolution: {resolution[0]} \n➥ Preset: {preset[0]} \n➥ Audio Bitrates: {audio_b[0]}\n➥ Upload Destination: {up_dest.capitalize()}")

    @app.on_message(filters.incoming & filters.command(["stop", f"stop@{BOT_USERNAME}"]))
    async def stop_handler(app, message):
        await on_task_complete()

    @app.on_message(filters.incoming & filters.command(["help", f"help@{BOT_USERNAME}"]) & is_auth)
    async def help_handler(app, message):
        stt = dt.now()
        ed = dt.now()
        v = ts((ed - uptime).total_seconds() * 1000)
        ms = (ed - stt).microseconds / 1000
        p = f"Ping = {ms}ms 🌋"
        await message.reply_text(
            Localisation.HELP_MESSAGE + f"\n\nBot Uptime = {v} 🚀\n{p}"
        )

    @app.on_message(filters.incoming & filters.command(["about", f"about@{BOT_USERNAME}"]) & is_auth)
    async def about_handler(app, message):
        await message.reply_text(Localisation.ABOUT_TEXT)

    app.add_handler(CallbackQueryHandler(main_callback_handler))
    
    async def startup():
        await init_bot()
        LOGGER.info("Bot started successfully!")
    
    app.loop.run_until_complete(startup())
    app.run()
