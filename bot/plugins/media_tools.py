from pyrogram import filters
from bot import BOT_USERNAME, app, merge_sessions
from bot.commands import Command
from bot.helper_funcs.utils import add_to_queue, is_auth


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
