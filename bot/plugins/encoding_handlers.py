from pyrogram import filters
from bot import AUTH_USERS, BOT_USERNAME, app
from bot.commands import Command
from bot.helper_funcs.utils import add_to_queue

@app.on_message(filters.incoming & filters.command([Command.COMPRESS, f"{Command.COMPRESS}@{BOT_USERNAME}"]))
async def compress_handler(client, message):
    if message.from_user.id not in AUTH_USERS:
        return await message.reply_text("🚫 Not authorized")

    reply = message.reply_to_message
    if not reply or not (reply.video or reply.document):
        return await message.reply_text("❌ Reply to a video or document to compress it.")

    await message.reply_text("⏰ Added to queue...", quote=True)
    await add_to_queue(reply, "compress")

@app.on_message(filters.incoming & filters.command([Command.P480, f"{Command.P480}@{BOT_USERNAME}"]))
async def p480_handler(client, message):
    if message.from_user.id not in AUTH_USERS:
        return await message.reply_text("🚫 Not authorized")
    reply = message.reply_to_message
    if not reply or not (reply.video or reply.document):
        return await message.reply_text("❌ Reply to a video or document.")
    await message.reply_text("⏰ Added 480p task to queue...", quote=True)
    await add_to_queue(reply, "480p")

@app.on_message(filters.incoming & filters.command([Command.P720, f"{Command.P720}@{BOT_USERNAME}", "720/"]))
async def p720_handler(client, message):
    if message.from_user.id not in AUTH_USERS:
        return await message.reply_text("🚫 Not authorized")
    reply = message.reply_to_message
    if not reply or not (reply.video or reply.document):
        return await message.reply_text("❌ Reply to a video or document.")
    await message.reply_text("⏰ Added 720p task to queue...", quote=True)
    await add_to_queue(reply, "720p")

@app.on_message(filters.incoming & filters.command([Command.P1080, f"{Command.P1080}@{BOT_USERNAME}"]))
async def p1080_handler(client, message):
    if message.from_user.id not in AUTH_USERS:
        return await message.reply_text("🚫 Not authorized")
    reply = message.reply_to_message
    if not reply or not (reply.video or reply.document):
        return await message.reply_text("❌ Reply to a video or document.")
    await message.reply_text("⏰ Added 1080p task to queue...", quote=True)
    await add_to_queue(reply, "1080p")

@app.on_message(filters.incoming & filters.command([Command.ALL, f"{Command.ALL}@{BOT_USERNAME}"]))
async def all_handler(client, message):
    if message.from_user.id not in AUTH_USERS:
        return await message.reply_text("🚫 Not authorized")
    reply = message.reply_to_message
    if not reply or not (reply.video or reply.document):
        return await message.reply_text("❌ Reply to a video or document.")
    await message.reply_text("⏰ Added all encoding tasks (480p, 720p, 1080p) to queue...", quote=True)
    await add_to_queue(reply, "480p")
    await add_to_queue(reply, "720p")
    await add_to_queue(reply, "1080p")
