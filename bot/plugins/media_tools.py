from pyrogram import filters
from bot import BOT_USERNAME, app, merge_sessions
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
    user_id = message.from_user.id
    reply = message.reply_to_message

    if user_id not in merge_sessions:
        merge_sessions[user_id] = []
        if reply and (reply.video or (reply.document and reply.document.mime_type and reply.document.mime_type.startswith("video/"))):
            merge_sessions[user_id].append(reply)
            return await message.reply_text("🆕 Merge session started with replied video.\nNow send more videos or use /done.")
        await message.reply_text("🆕 Merge session started.\nNow send all the videos you want to merge one by one, then send /done.")
    else:
        if reply and (reply.video or (reply.document and reply.document.mime_type and reply.document.mime_type.startswith("video/"))):
            merge_sessions[user_id].append(reply)
            return await message.reply_text(f"✅ Replied video added. Total: {len(merge_sessions[user_id])}\nSend more or use /done.")
        await message.reply_text(f"🎬 You have {len(merge_sessions[user_id])} videos in your merge session.\nSend more or use /done to merge.")

@app.on_message(filters.incoming & filters.command([Command.DONE, f"{Command.DONE}@{BOT_USERNAME}"]) & is_auth)
async def done_handler(client, message):
    user_id = message.from_user.id
    if user_id not in merge_sessions or not merge_sessions[user_id]:
        return await message.reply_text("❌ No videos in your merge session. Use /merge to start.")

    video_messages = merge_sessions[user_id]
    if len(video_messages) < 2:
        return await message.reply_text(f"❌ Need at least two videos to merge. Currently have {len(video_messages)}.")

    await message.reply_text(f"⏰ Added merge task ({len(video_messages)} videos) to queue...", quote=True)
    await add_to_queue(message, "merge", options={'video_messages': video_messages})

    # Session is cleared in handle_merge_task or here?
    # Better here to allow user to start new session immediately
    del merge_sessions[user_id]

@app.on_message(filters.incoming & (filters.video | filters.document) & is_auth, group=-1)
async def collect_videos_for_merge(client, message):
    user_id = message.from_user.id
    if user_id in merge_sessions:
        if message.video or (message.document and message.document.mime_type and message.document.mime_type.startswith("video/")):
            merge_sessions[user_id].append(message)
            await message.reply_text(f"✅ Video added to merge session. Total: {len(merge_sessions[user_id])}\nSend more or use /done to merge.", quote=True)
            message.stop_propagation()
