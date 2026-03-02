from pyrogram import filters
from bot import BOT_USERNAME, app
from bot.commands import Command
from bot.helper_funcs.utils import add_to_queue, is_auth, style_text

@app.on_message(filters.incoming & filters.command([Command.COMPRESS, f"{Command.COMPRESS}@{BOT_USERNAME}"]) & is_auth)
async def compress_handler(client, message):
    media = message.reply_to_message or message
    if not (media.video or media.document):
        return await message.reply_text("❌ " + style_text("Reply to a video or document to compress it."))

    await message.reply_text("⏰ " + style_text("Added to queue..."), quote=True)
    await add_to_queue(media, "compress")

@app.on_message(filters.incoming & filters.command([Command.P480, f"{Command.P480}@{BOT_USERNAME}"]) & is_auth)
async def p480_handler(client, message):
    media = message.reply_to_message or message
    if not (media.video or media.document):
        return await message.reply_text("❌ " + style_text("Reply to a video or document."))
    await message.reply_text("⏰ " + style_text("Added 480p task to queue..."), quote=True)
    await add_to_queue(media, "480p")

@app.on_message(filters.incoming & filters.command([Command.P720, f"{Command.P720}@{BOT_USERNAME}"]) & is_auth)
async def p720_handler(client, message):
    media = message.reply_to_message or message
    if not (media.video or media.document):
        return await message.reply_text("❌ " + style_text("Reply to a video or document."))
    await message.reply_text("⏰ " + style_text("Added 720p task to queue..."), quote=True)
    await add_to_queue(media, "720p")

@app.on_message(filters.incoming & filters.command([Command.P1080, f"{Command.P1080}@{BOT_USERNAME}"]) & is_auth)
async def p1080_handler(client, message):
    media = message.reply_to_message or message
    if not (media.video or media.document):
        return await message.reply_text("❌ " + style_text("Reply to a video or document."))
    await message.reply_text("⏰ " + style_text("Added 1080p task to queue..."), quote=True)
    await add_to_queue(media, "1080p")

@app.on_message(filters.incoming & filters.command([Command.ALL, f"{Command.ALL}@{BOT_USERNAME}"]) & is_auth)
async def all_handler(client, message):
    media = message.reply_to_message or message
    if not (media.video or media.document):
        return await message.reply_text("❌ " + style_text("Reply to a video or document."))
    await message.reply_text("⏰ " + style_text("Added all-in-one multi-resolution task (480p, 720p, 1080p) to queue..."), quote=True)
    await add_to_queue(media, "all_resolutions")
