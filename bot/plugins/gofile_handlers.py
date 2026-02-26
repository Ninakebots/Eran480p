import os
import time
import logging
from pyrogram import filters
from bot import BOT_USERNAME, app, GOFILE_TOKEN
from bot.commands import Command
from bot.helper_funcs.utils import is_auth, hbs
from bot.helper_funcs.display_progress import progress_for_pyrogram
from bot.helper_funcs.gofile import upload_gofile

LOGGER = logging.getLogger(__name__)

@app.on_message(filters.incoming & filters.command([Command.GOFILE, f"{Command.GOFILE}@{BOT_USERNAME}"]) & is_auth)
async def gofile_handler(client, message):
    if not message.from_user:
        return

    reply = message.reply_to_message
    if not reply or not (reply.video or reply.document or reply.audio or reply.animation):
        return await message.reply_text("❌ Reply to a file to upload it to Gofile.io.")

    sent_message = await message.reply_text("📥 **Downloading file...**", quote=True)

    file_path = None
    try:
        start_time = time.time()
        file_path = await client.download_media(
            message=reply,
            progress=progress_for_pyrogram,
            progress_args=(client, "📥 **Downloading...**", sent_message, start_time)
        )

        if not file_path:
            return await sent_message.edit_text("❌ Download failed.")

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
            await sent_message.edit_text("❌ Gofile upload failed.")

    except Exception as e:
        LOGGER.error(f"Error in gofile_handler: {e}")
        try:
            await sent_message.edit_text(f"❌ Error: {e}")
        except:
            pass
    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
