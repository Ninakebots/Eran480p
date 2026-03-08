import os, time
from pyrogram import filters
from bot import BOT_USERNAME, app, merge_sessions, zip_sessions, batch_sessions
from bot.commands import Command
from bot.helper_funcs.utils import add_to_queue, is_auth, style_text


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

@app.on_message(filters.incoming & filters.command([Command.MEDIAINFO, f"{Command.MEDIAINFO}@{BOT_USERNAME}"]) & is_auth)
async def mediainfo_handler(client, message):
    if not message.from_user:
        return
    reply = message.reply_to_message
    if not reply or not (reply.video or reply.document):
        return await message.reply_text("❌ Reply to a video.")
    await message.reply_text("⏰ Fetching media info...", quote=True)
    await add_to_queue(reply, "mediainfo")

@app.on_message(filters.incoming & filters.command([Command.MERGE, Command.MARGE, f"{Command.MERGE}@{BOT_USERNAME}", f"{Command.MARGE}@{BOT_USERNAME}"]) & is_auth)
async def merge_handler(client, message):
    if not message.from_user: return
    user_id = message.from_user.id
    reply = message.reply_to_message

    if user_id in zip_sessions or user_id in batch_sessions:
        return await message.reply_text("⚠️ You already have another session active. Use /done to finish it first.")

    if user_id not in merge_sessions:
        merge_sessions[user_id] = []
        if reply and (reply.video or reply.audio or (reply.document and reply.document.mime_type and (reply.document.mime_type.startswith("video/") or reply.document.mime_type.startswith("audio/")))):
            merge_sessions[user_id].append(reply)
            return await message.reply_text(f"🆕 **{style_text('Merge session started!')}**\nNow send more files or use /done.")
        await message.reply_text(f"🆕 **{style_text('Merge session started!')}**\nNow send all files you want to merge one by one, then send /done.")
    else:
        await message.reply_text(f"🎬 {style_text('You have')} {len(merge_sessions[user_id])} {style_text('files in your merge session.')}\nSend more or use /done to merge.")

@app.on_message(filters.incoming & filters.command([Command.BATCH, f"{Command.BATCH}@{BOT_USERNAME}"]) & is_auth)
async def batch_handler(client, message):
    if not message.from_user: return
    user_id = message.from_user.id
    reply = message.reply_to_message

    if user_id in merge_sessions or user_id in zip_sessions:
        return await message.reply_text("⚠️ You already have another session active. Use /done to finish it first.")

    if user_id not in batch_sessions:
        batch_sessions[user_id] = []
        if reply and (reply.video or reply.audio or reply.document or reply.animation):
            batch_sessions[user_id].append(reply)
            return await message.reply_text(f"🆕 **{style_text('Batch session started!')}**\nNow send more files to process individually, then send /done.")
        await message.reply_text(f"🆕 **{style_text('Batch session started!')}**\nNow send all files you want to process one by one, then send /done.")
    else:
        await message.reply_text(f"📦 {style_text('You have')} {len(batch_sessions[user_id])} {style_text('files in your batch session.')}\nSend more or use /done to start processing.")

@app.on_message(filters.incoming & filters.command([Command.DONE, f"{Command.DONE}@{BOT_USERNAME}"]) & is_auth)
async def done_handler(client, message):
    if not message.from_user: return
    user_id = message.from_user.id

    if user_id in merge_sessions:
        file_messages = merge_sessions[user_id]
        if len(file_messages) < 2:
            return await message.reply_text(f"❌ Need at least two files to merge. Currently have {len(file_messages)}.")
        await message.reply_text(f"⏰ Added merge task ({len(file_messages)} files) to queue...", quote=True)
        await add_to_queue(message, "merge", options={'video_messages': file_messages})
        del merge_sessions[user_id]

    elif user_id in zip_sessions:
        file_messages = zip_sessions[user_id]
        if not file_messages:
            return await message.reply_text("❌ No files in your zip session.")
        await message.reply_text(f"⏰ Added zip task ({len(file_messages)} files) to queue...", quote=True)
        await add_to_queue(message, "zip", options={'file_messages': file_messages})
        del zip_sessions[user_id]

    elif user_id in batch_sessions:
        file_messages = batch_sessions[user_id]
        if not file_messages:
            return await message.reply_text("❌ No files in your batch session.")

        await message.reply_text(f"🚀 Adding {len(file_messages)} tasks to queue...")
        for msg in file_messages:
            # Determine task type (default to compress)
            await add_to_queue(msg, "compress")
        del batch_sessions[user_id]

    else:
        await message.reply_text("❌ No active session found. Use /merge, /zip or /batch to start.")

@app.on_message(filters.incoming & filters.command([Command.SAVETHUMB, f"{Command.SAVETHUMB}@{BOT_USERNAME}"]) & is_auth)
async def savethumb_handler(client, message):
    if not message.from_user:
        return
    user_id = message.from_user.id
    reply = message.reply_to_message
    if not reply or not reply.photo:
        return await message.reply_text("❌ Reply to a photo to save it as custom thumbnail.")

    thumb_dir = "thumbnails"
    os.makedirs(thumb_dir, exist_ok=True)
    thumb_path = os.path.join(thumb_dir, f"{user_id}.jpg")

    await client.download_media(message=reply.photo, file_name=thumb_path)
    await message.reply_text("✅ Custom thumbnail saved.")

@app.on_message(filters.incoming & filters.command([Command.DELTHUMB, "remthumb", "remove_thumbnail", f"{Command.DELTHUMB}@{BOT_USERNAME}"]) & is_auth)
async def delthumb_handler(client, message):
    if not message.from_user:
        return
    user_id = message.from_user.id
    thumb_path = os.path.join("thumbnails", f"{user_id}.jpg")
    if os.path.exists(thumb_path):
        os.remove(thumb_path)
        await message.reply_text("✅ Custom thumbnail deleted.")
    else:
        await message.reply_text("❌ No custom thumbnail found.")

@app.on_message(filters.incoming & filters.command([Command.VIEWTHUMB, f"{Command.VIEWTHUMB}@{BOT_USERNAME}"]) & is_auth)
async def viewthumb_handler(client, message):
    if not message.from_user:
        return
    user_id = message.from_user.id
    thumb_path = os.path.join("thumbnails", f"{user_id}.jpg")
    if os.path.exists(thumb_path):
        await message.reply_photo(photo=thumb_path, caption="🖼 **Your Current Custom Thumbnail**")
    else:
        await message.reply_text("❌ No custom thumbnail found.")

@app.on_message(filters.incoming & filters.command([Command.SETWATERMARK, f"{Command.SETWATERMARK}@{BOT_USERNAME}"]) & is_auth)
async def setwatermark_handler(client, message):
    if not message.from_user:
        return
    user_id = message.from_user.id
    reply = message.reply_to_message

    if not reply or not (reply.photo or reply.document):
        return await message.reply_text("❌ Reply to a photo or document (transparent PNG recommended) to set it as watermark.")

    media = reply.photo or reply.document
    if reply.document and not (reply.document.mime_type and reply.document.mime_type.startswith("image/")):
        return await message.reply_text("❌ The replied document must be an image.")

    wm_dir = "watermarks"
    os.makedirs(wm_dir, exist_ok=True)
    wm_path = os.path.join(wm_dir, f"{user_id}.png")

    await client.download_media(message=media, file_name=wm_path)
    await message.reply_text("✅ Custom watermark saved.")

@app.on_message(filters.incoming & filters.command([Command.REMWATERMARK, "remwatermark", f"{Command.REMWATERMARK}@{BOT_USERNAME}"]) & is_auth)
async def remwatermark_handler(client, message):
    if not message.from_user:
        return
    user_id = message.from_user.id
    wm_path = os.path.join("watermarks", f"{user_id}.png")
    if os.path.exists(wm_path):
        os.remove(wm_path)
        await message.reply_text("✅ Custom watermark deleted.")
    else:
        await message.reply_text("❌ No custom watermark found.")

@app.on_message(filters.incoming & filters.command([Command.VIEWWATERMARK, f"{Command.VIEWWATERMARK}@{BOT_USERNAME}"]) & is_auth)
async def viewwatermark_handler(client, message):
    if not message.from_user:
        return
    user_id = message.from_user.id
    wm_path = os.path.join("watermarks", f"{user_id}.png")
    if os.path.exists(wm_path):
        await message.reply_photo(photo=wm_path, caption="🖼 **Your Current Custom Watermark**")
    else:
        await message.reply_text("❌ No custom watermark found.")

@app.on_message(filters.incoming & filters.command([Command.RENAME, f"{Command.RENAME}@{BOT_USERNAME}"]) & is_auth)
async def rename_handler(client, message):
    reply = message.reply_to_message
    if not reply or not (reply.video or reply.audio or reply.document or reply.animation):
        return await message.reply_text("❌ Reply to a file to rename it.")

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        return await message.reply_text("❌ Usage: `/rename new_file_name.mp4`")

    new_name = args[1]
    await add_to_queue(reply, "rename", options={'new_name': new_name})
    await message.reply_text(f"⏰ Added rename task to queue.\nNew Name: `{new_name}`")

@app.on_message(filters.incoming & filters.command([Command.ZIP, f"{Command.ZIP}@{BOT_USERNAME}"]) & is_auth)
async def zip_cmd(client, message):
    if not message.from_user: return
    user_id = message.from_user.id
    reply = message.reply_to_message

    if user_id in merge_sessions or user_id in batch_sessions:
        return await message.reply_text("⚠️ You already have another session active. Use /done to finish it first.")

    if user_id not in zip_sessions:
        zip_sessions[user_id] = []
        if reply and (reply.video or reply.audio or reply.document or reply.animation or reply.photo):
            zip_sessions[user_id].append(reply)
            return await message.reply_text(f"🆕 **{style_text('Zip session started!')}**\nNow send more files to zip together, then send /done.")
        await message.reply_text(f"🆕 **{style_text('Zip session started!')}**\nNow send all files you want to zip one by one, then send /done.")
    else:
        await message.reply_text(f"🗜️ {style_text('You have')} {len(zip_sessions[user_id])} {style_text('files in your zip session.')}\nSend more or use /done to zip.")

@app.on_message(filters.incoming & (filters.video | filters.audio | filters.document | filters.animation | filters.photo) & is_auth, group=-1)
async def collect_media_handler(client, message):
    if not message.from_user: return
    user_id = message.from_user.id

    if user_id in merge_sessions:
        if message.video or message.audio or (message.document and message.document.mime_type and (message.document.mime_type.startswith("video/") or message.document.mime_type.startswith("audio/"))):
            merge_sessions[user_id].append(message)
            await message.reply_text(f"✅ File added to merge. Total: {len(merge_sessions[user_id])}", quote=True)
            message.stop_propagation()

    elif user_id in zip_sessions:
        zip_sessions[user_id].append(message)
        await message.reply_text(f"✅ File added to zip. Total: {len(zip_sessions[user_id])}", quote=True)
        message.stop_propagation()

    elif user_id in batch_sessions:
        batch_sessions[user_id].append(message)
        await message.reply_text(f"✅ File added to batch. Total: {len(batch_sessions[user_id])}", quote=True)
        message.stop_propagation()
