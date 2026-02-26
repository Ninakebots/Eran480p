from pyrogram import filters
from bot import BOT_USERNAME, app, merge_sessions
from bot.commands import Command
from bot.helper_funcs.utils import add_to_queue, is_auth


@app.on_message(filters.incoming & filters.command([Command.EXTRACT_AUDIO, f"{Command.EXTRACT_AUDIO}@{BOT_USERNAME}"]) & is_auth)
async def extract_audio_cmd(client, message):
    reply = message.reply_to_message
    if not reply or not (reply.video or (reply.document and reply.document.mime_type and reply.document.mime_type.startswith("video/"))):
        return await message.reply_text("❌ Reply to a video to extract audio.")
    await add_to_queue(reply, "extract_audio")
    await message.reply_text("⏰ Added audio extraction task to queue.")

@app.on_message(filters.incoming & filters.command([Command.EXTRACT_SUB, f"{Command.EXTRACT_SUB}@{BOT_USERNAME}"]) & is_auth)
async def extract_sub_cmd(client, message):
    reply = message.reply_to_message
    if not reply or not (reply.video or (reply.document and reply.document.mime_type and reply.document.mime_type.startswith("video/"))):
        return await message.reply_text("❌ Reply to a video to extract subtitles.")
    await add_to_queue(reply, "extract_sub")
    await message.reply_text("⏰ Added subtitle extraction task to queue.")

@app.on_message(filters.incoming & filters.command([Command.ADDAUDIO, f"{Command.ADDAUDIO}@{BOT_USERNAME}"]) & is_auth)
async def add_audio_cmd(client, message):
    reply = message.reply_to_message
    if not reply or not (reply.audio or (reply.document and reply.document.mime_type and reply.document.mime_type.startswith("audio/"))):
        return await message.reply_text("❌ Reply to an audio file which is itself a reply to a video file.")

    video_message = reply.reply_to_message
    if not video_message or not (video_message.video or (video_message.document and video_message.document.mime_type and video_message.document.mime_type.startswith("video/"))):
        return await message.reply_text("❌ The replied audio must be a reply to a video file.")

    await add_to_queue(video_message, "add_audio", options={'audio_message': reply})
    await message.reply_text("⏰ Added 'add audio' task to queue.")

@app.on_message(filters.incoming & filters.command([Command.REMAUDIO, f"{Command.REMAUDIO}@{BOT_USERNAME}"]) & is_auth)
async def remaudio_cmd(client, message):
    reply = message.reply_to_message
    if not reply or not (reply.video or (reply.document and reply.document.mime_type and reply.document.mime_type.startswith("video/"))):
        return await message.reply_text("❌ Reply to a video to remove audio.")
    await add_to_queue(reply, "remove_audio")
    await message.reply_text("⏰ Added 'remove audio' task to queue.")

@app.on_message(filters.incoming & filters.command([Command.RSUB, f"{Command.RSUB}@{BOT_USERNAME}"]) & is_auth)
async def rsub_cmd(client, message):
    reply = message.reply_to_message
    if not reply or not (reply.video or (reply.document and reply.document.mime_type and reply.document.mime_type.startswith("video/"))):
        return await message.reply_text("❌ Reply to a video to remove subtitles.")
    await add_to_queue(reply, "remove_sub")
    await message.reply_text("⏰ Added 'remove subtitles' task to queue.")

@app.on_message(filters.incoming & filters.command([Command.TRIM, f"{Command.TRIM}@{BOT_USERNAME}"]) & is_auth)
async def trim_cmd(client, message):
    reply = message.reply_to_message
    if not reply or not (reply.video or (reply.document and reply.document.mime_type and reply.document.mime_type.startswith("video/"))):
        return await message.reply_text("❌ Reply to a video to trim.")

    args = message.text.split()
    if len(args) < 3:
        return await message.reply_text("❌ Usage: `/trim 00:00:00 00:00:10` (Start - End)")

    start_time = args[1]
    end_time = args[2]

    await add_to_queue(reply, "trim", options={'start_time': start_time, 'end_time': end_time})
    await message.reply_text(f"⏰ Added trim task ({start_time} - {end_time}) to queue.")

@app.on_message(filters.incoming & filters.command([Command.COMPOSE, "Compose", f"{Command.COMPOSE}@{BOT_USERNAME}"]) & is_auth)
async def compose_handler(client, message):
    # Alias for merge for now as it's the most common "composition"
    await merge_handler(client, message)

@app.on_message(filters.incoming & filters.command([Command.MEDIAINFO, f"{Command.MEDIAINFO}@{BOT_USERNAME}"]) & is_auth)
async def mediainfo_handler(client, message):
    if not message.from_user:
        return
    reply = message.reply_to_message
    if not reply or not (reply.video or reply.document):
        return await message.reply_text("❌ Reply to a video.")
    await message.reply_text("⏰ Fetching media info...", quote=True)
    await add_to_queue(reply, "mediainfo")

@app.on_message(filters.incoming & filters.command([Command.MERGE, f"{Command.MERGE}@{BOT_USERNAME}"]) & is_auth)
async def merge_handler(client, message):
    if not message.from_user:
        return
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
    if not message.from_user:
        return
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
    if not message.from_user:
        return
    user_id = message.from_user.id
    if user_id in merge_sessions:
        if message.video or (message.document and message.document.mime_type and message.document.mime_type.startswith("video/")):
            merge_sessions[user_id].append(message)
            await message.reply_text(f"✅ Video added to merge session. Total: {len(merge_sessions[user_id])}\nSend more or use /done to merge.", quote=True)
            message.stop_propagation()
