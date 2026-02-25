from pyrogram import filters
from bot import BOT_USERNAME, app
from bot.commands import Command
from bot.helper_funcs.utils import add_to_queue, is_auth

@app.on_message(filters.incoming & filters.command([Command.EXTRACT_AUDIO, f"{Command.EXTRACT_AUDIO}@{BOT_USERNAME}"]) & is_auth)
async def extract_audio_handler(client, message):
    reply = message.reply_to_message
    if not reply or not (reply.video or reply.document):
        return await message.reply_text("❌ Reply to a video.")
    await message.reply_text("⏰ Added audio extraction task to queue...", quote=True)
    await add_to_queue(reply, "extract_audio")

@app.on_message(filters.incoming & filters.command([Command.ADDAUDIO, f"{Command.ADDAUDIO}@{BOT_USERNAME}"]) & is_auth)
async def add_audio_handler(client, message):
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

@app.on_message(filters.incoming & filters.command([Command.REMAUDIO, f"{Command.REMAUDIO}@{BOT_USERNAME}"]) & is_auth)
async def remaudio_handler(client, message):
    reply = message.reply_to_message
    if not reply or not (reply.video or reply.document):
        return await message.reply_text("❌ Reply to a video.")
    await message.reply_text("⏰ Added remove-audio task to queue...", quote=True)
    await add_to_queue(reply, "remove_audio")

@app.on_message(filters.incoming & filters.command([Command.SUB, f"{Command.SUB}@{BOT_USERNAME}"]) & is_auth)
async def sub_handler(client, message):
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

@app.on_message(filters.incoming & filters.command([Command.HSUB, f"{Command.HSUB}@{BOT_USERNAME}"]) & is_auth)
async def hsub_handler(client, message):
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

@app.on_message(filters.incoming & filters.command([Command.RSUB, f"{Command.RSUB}@{BOT_USERNAME}"]) & is_auth)
async def rsub_handler(client, message):
    reply = message.reply_to_message
    if not reply or not (reply.video or reply.document):
        return await message.reply_text("❌ Reply to a video.")
    await message.reply_text("⏰ Added remove-sub task to queue...", quote=True)
    await add_to_queue(reply, "remove_sub")

@app.on_message(filters.incoming & filters.command([Command.TRIM, f"{Command.TRIM}@{BOT_USERNAME}"]) & is_auth)
async def trim_handler(client, message):
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

@app.on_message(filters.incoming & filters.command([Command.MEDIAINFO, f"{Command.MEDIAINFO}@{BOT_USERNAME}"]) & is_auth)
async def mediainfo_handler(client, message):
    reply = message.reply_to_message
    if not reply or not (reply.video or reply.document):
        return await message.reply_text("❌ Reply to a video.")
    await message.reply_text("⏰ Fetching media info...", quote=True)
    await add_to_queue(reply, "mediainfo")

@app.on_message(filters.incoming & filters.command([Command.MERGE, f"{Command.MERGE}@{BOT_USERNAME}"]) & is_auth)
async def merge_handler(client, message):
    reply = message.reply_to_message
    if not reply or not (reply.video or reply.document):
        return await message.reply_text("❌ Reply to the last video in the chain to merge.")

    # Traverse the reply chain to find all videos
    video_messages = []
    current = reply

    while current:
        if current.video or (current.document and current.document.mime_type.startswith("video/")):
            video_messages.append(current)
        else:
            break

        if current.reply_to_message:
            # We need to fetch the full message to get the media
            current = await client.get_messages(chat_id=current.chat.id, message_ids=current.reply_to_message.id)
        else:
            break

    if len(video_messages) < 2:
        return await message.reply_text("❌ Need at least two videos in a reply chain to merge.")

    # We want to merge in the order they were sent (top to bottom)
    video_messages.reverse()

    await message.reply_text(f"⏰ Added merge task ({len(video_messages)} videos) to queue...", quote=True)
    await add_to_queue(message, "merge", options={'video_messages': video_messages})
