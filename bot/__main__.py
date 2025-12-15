from datetime import datetime as dt
import os
import logging
from pyrogram import filters
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.types import CallbackQuery

from bot import (
    APP_ID, API_HASH, AUTH_USERS, DOWNLOAD_LOCATION, LOGGER, TG_BOT_TOKEN, BOT_USERNAME, SESSION_NAME, data, app, AUTH_CHATS, 
    crf, resolution, audio_b, preset, codec
)
from bot.helper_funcs.utils import add_task, on_task_complete, sysinfo
from bot.helper_funcs.database import db
from bot.plugins.incoming_message_fn import incoming_start_message_f, incoming_compress_message_f, incoming_cancel_message_f
from bot.plugins.status_message_fn import eval_message_f, exec_message_f, upload_log_file
from bot.plugins.call_back_button_handler import button as admin_button_handler
from bot.watermark_handlers import *
from bot.commands import Command

# Configure logging to reduce MongoDB verbosity
logging.getLogger("pymongo").setLevel(logging.WARNING)
logging.getLogger("motor").setLevel(logging.WARNING)

crf.append("25")
codec.append("libx264")
resolution.append("1920x1080")
preset.append("veryfast")
audio_b.append("48k")

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

    app.add_handler(MessageHandler(incoming_start_message_f, filters.command(["start", f"start@{BOT_USERNAME}"])))

    @app.on_message(filters.incoming & filters.command(["crf", f"crf@{BOT_USERNAME}"]))
    async def changecrf(app, message):
        if message.chat.id in AUTH_USERS:
            cr = message.text.split(" ", maxsplit=1)[1]
            crf.insert(0, f"{cr}")
            await message.reply_text(f"📊 I will be using : {cr} crf")
        else:
            await message.reply_text("🔒 Admin Only")

    @app.on_message(filters.incoming & filters.command(["resolution", f"resolution@{BOT_USERNAME}"]))
    async def changer(app, message):
        if message.chat.id in AUTH_USERS:
            r = message.text.split(" ", maxsplit=1)[1]
            resolution.insert(0, f"{r}")
            await message.reply_text(f"🎬 I will be using : {r}")
        else:
            await message.reply_text("🔒 Admin Only")

    @app.on_message(filters.incoming & filters.command(["preset", f"preset@{BOT_USERNAME}"]))
    async def changepr(app, message):
        if message.chat.id in AUTH_USERS:
            pop = message.text.split(" ", maxsplit=1)[1]
            preset.insert(0, f"{pop}")
            await message.reply_text(f"⚡ I will be using : {pop} preset")
        else:
            await message.reply_text("🔒 Admin Only")

    @app.on_message(filters.incoming & filters.command(["codec", f"codec@{BOT_USERNAME}"]))
    async def changecode(app, message):
        if message.chat.id in AUTH_USERS:
            col = message.text.split(" ", maxsplit=1)[1]
            codec.insert(0, f"{col}")
            await message.reply_text(f"🎥 I will be using : {col} codec")
        else:
            await message.reply_text("🔒 Admin Only")

    @app.on_message(filters.incoming & filters.command(["audio", f"audio@{BOT_USERNAME}"]))
    async def changea(app, message):
        if message.chat.id in AUTH_USERS:
            aud = message.text.split(" ", maxsplit=1)[1]
            audio_b.insert(0, f"{aud}")
            await message.reply_text(f"🎵 I will be using : {aud} audio")
        else:
            await message.reply_text("🔒 Admin Only")

    @app.on_message(filters.incoming & filters.command(["compress", f"compress@{BOT_USERNAME}"]))
    async def compress_handler(app, message):
        if message.chat.id not in AUTH_USERS:
            return await message.reply_text("🚫 You are not authorized to use this bot")
        query = await message.reply_text("⏰ Added to queue...\nPlease be patient, compression will start soon", quote=True)
        data.append(message.reply_to_message)
        if len(data) == 1:
            await query.delete()
            await add_task(message.reply_to_message)

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

    @app.on_message(filters.incoming & (filters.video | filters.document))
    async def video_or_document_handler(app, message):
        if message.chat.id not in AUTH_USERS:
            return await message.reply_text("🚫 Not authorized")
        query = await message.reply_text("⏰ Added to queue...\nPlease be patient, compression will start soon", quote=True)
        data.append(message)
        if len(data) == 1:
            await query.delete()
            await add_task(message)

    @app.on_message(filters.incoming & filters.command(["settings", f"settings@{BOT_USERNAME}"]))
    async def settings(app, message):
        if message.chat.id in AUTH_USERS:
            await message.reply_text(f"⚙️ Current Settings:\n\n➥ Codec: {codec[0]} \n➥ Crf: {crf[0]} \n➥ Resolution: {resolution[0]} \n➥ Preset: {preset[0]} \n➥ Audio Bitrates: {audio_b[0]}")
        else:
            await message.reply_text("🔒 Admin Only")

    @app.on_message(filters.incoming & filters.command(["sysinfo", f"sysinfo@{BOT_USERNAME}"]))
    async def sysinfo_handler(app, message):
        if message.chat.id in AUTH_USERS:
            await sysinfo(message)
        else:
            await message.reply_text("🔒 Admin Only")

    @app.on_message(filters.incoming & filters.command(["cancel", f"cancel@{BOT_USERNAME}"]))
    async def cancel_handler(app, message):
        await incoming_cancel_message_f(app, message)

    @app.on_message(filters.incoming & filters.command(["exec", f"exec@{BOT_USERNAME}"]))
    async def exec_handler(app, message):
        await exec_message_f(app, message)

    @app.on_message(filters.incoming & filters.command(["eval", f"eval@{BOT_USERNAME}"]))
    async def eval_handler(app, message):
        await eval_message_f(app, message)

    @app.on_message(filters.incoming & filters.command(["stop", f"stop@{BOT_USERNAME}"]))
    async def stop_handler(app, message):
        await on_task_complete()

    @app.on_message(filters.incoming & filters.command(["help", f"help@{BOT_USERNAME}"]))
    async def help_handler(app, message):
        stt = dt.now()
        ed = dt.now()
        v = ts((ed - uptime).total_seconds() * 1000)
        ms = (ed - stt).microseconds / 1000
        p = f"Ping = {ms}ms 🌋"
        await message.reply_text(
            f"Hi, I am Video Compressor Bot\n\n"
            f"➥ Send me your Telegram files\n"
            f"➥ I will encode them one by one using the queue feature\n"
            f"➥ Use `/{Command.SET_WATERMARK} <image_url>` to set watermark\n"
            f"➥ Use `/{Command.CHECK_WATERMARK}` to check current watermark\n"
            f"➥ Use `/{Command.SET_WATERMARK} remove` to remove watermark\n\n"
            f"Bot Uptime = {v} 🚀\n{p}"
        )

    app.add_handler(CallbackQueryHandler(main_callback_handler))
    
    async def startup():
        await init_bot()
        LOGGER.info("Bot started successfully!")
    
    app.loop.run_until_complete(startup())
    app.run()
