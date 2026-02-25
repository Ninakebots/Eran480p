from pyrogram import filters
from bot import AUTH_USERS, BOT_USERNAME, app
from bot.commands import Command
from bot.helper_funcs.utils import add_to_queue

@app.on_message(filters.incoming & filters.command([Command.EXTRACT_AUDIO, f"{Command.EXTRACT_AUDIO}@{BOT_USERNAME}"]))
async def extract_audio_handler(client, message):
    if message.from_user.id not in AUTH_USERS:
        return
    reply = message.reply_to_message
    if not reply or not (reply.video or reply.document):
        return await message.reply_text("❌ Reply to a video.")
    await message.reply_text("⏰ Added audio extraction task to queue...", quote=True)
    await add_to_queue(reply, "extract_audio")

@app.on_message(filters.incoming & filters.command([Command.ADDAUDIO, f"{Command.ADDAUDIO}@{BOT_USERNAME}"]))
async def add_audio_handler(client, message):
    if message.from_user.id not in AUTH_USERS:
        return
    reply = message.reply_to_message
    if not reply or not (reply.audio or reply.document):
        return await message.reply_text("❌ Reply to an audio file to add it to a video.")

    video_message = None
    if reply.reply_to_message and (reply.reply_to_message.video or reply.reply_to_message.document):
        video_message = reply.reply_to_message

    if not video_message:
        return await message.reply_text("❌ Please reply to an audio file which is itself a reply to a video file.")

    await message.reply_text("⏰ Added add-audio task to queue...", quote=True)
    await add_to_queue(video_message, "add_audio", options={'audio_message': reply})

@app.on_message(filters.incoming & filters.command([Command.REMAUDIO, f"{Command.REMAUDIO}@{BOT_USERNAME}"]))
async def remaudio_handler(client, message):
    if message.from_user.id not in AUTH_USERS:
        return
    reply = message.reply_to_message
    if not reply or not (reply.video or reply.document):
        return await message.reply_text("❌ Reply to a video.")
    await message.reply_text("⏰ Added remove-audio task to queue...", quote=True)
    await add_to_queue(reply, "remove_audio")

@app.on_message(filters.incoming & filters.command([Command.SUB, f"{Command.SUB}@{BOT_USERNAME}"]))
async def sub_handler(client, message):
    if message.from_user.id not in AUTH_USERS:
        return
    reply = message.reply_to_message
    if not reply or not reply.document:
        return await message.reply_text("❌ Reply to a subtitle file (.srt/.ass).")

    video_message = None
    if reply.reply_to_message and (reply.reply_to_message.video or reply.reply_to_message.document):
        video_message = reply.reply_to_message

    if not video_message:
        return await message.reply_text("❌ Please reply to a subtitle file which is itself a reply to a video file.")

    await message.reply_text("⏰ Added soft-sub task to queue...", quote=True)
    await add_to_queue(video_message, "add_soft_sub", options={'sub_message': reply})

@app.on_message(filters.incoming & filters.command([Command.HSUB, f"{Command.HSUB}@{BOT_USERNAME}"]))
async def hsub_handler(client, message):
    if message.from_user.id not in AUTH_USERS:
        return
    reply = message.reply_to_message
    if not reply or not reply.document:
        return await message.reply_text("❌ Reply to a subtitle file (.srt/.ass).")

    video_message = None
    if reply.reply_to_message and (reply.reply_to_message.video or reply.reply_to_message.document):
        video_message = reply.reply_to_message

    if not video_message:
        return await message.reply_text("❌ Please reply to a subtitle file which is itself a reply to a video file.")

    await message.reply_text("⏰ Added hard-sub task to queue...", quote=True)
    await add_to_queue(video_message, "add_hard_sub", options={'sub_message': reply})

@app.on_message(filters.incoming & filters.command([Command.RSUB, f"{Command.RSUB}@{BOT_USERNAME}"]))
async def rsub_handler(client, message):
    if message.from_user.id not in AUTH_USERS:
        return
    reply = message.reply_to_message
    if not reply or not (reply.video or reply.document):
        return await message.reply_text("❌ Reply to a video.")
    await message.reply_text("⏰ Added remove-sub task to queue...", quote=True)
    await add_to_queue(reply, "remove_sub")

@app.on_message(filters.incoming & filters.command([Command.TRIM, f"{Command.TRIM}@{BOT_USERNAME}"]))
async def trim_handler(client, message):
    if message.from_user.id not in AUTH_USERS:
        return
    reply = message.reply_to_message
    if not reply or not (reply.video or reply.document):
        return await message.reply_text("❌ Reply to a video.")

    args = message.text.split(" ")
    if len(args) < 3:
        return await message.reply_text("❌ Usage: `/trim start_time end_time` (e.g., `/trim 00:01:00 00:02:30`)")

    start_time = args[1]
    end_time = args[2]

    await message.reply_text(f"⏰ Added trim task ({start_time} - {end_time}) to queue...", quote=True)
    await add_to_queue(reply, "trim", options={'start_time': start_time, 'end_time': end_time})

@app.on_message(filters.incoming & filters.command([Command.MEDIAINFO, f"{Command.MEDIAINFO}@{BOT_USERNAME}"]))
async def mediainfo_handler(client, message):
    if message.from_user.id not in AUTH_USERS:
        return
    reply = message.reply_to_message
    if not reply or not (reply.video or reply.document):
        return await message.reply_text("❌ Reply to a video.")
    await message.reply_text("⏰ Fetching media info...", quote=True)
    await add_to_queue(reply, "mediainfo")
