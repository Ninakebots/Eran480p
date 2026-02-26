import logging
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot import BOT_USERNAME, app, subtitle_sessions
from bot.commands import Command
from bot.helper_funcs.utils import remove_from_queue, is_auth

LOGGER = logging.getLogger(__name__)

@app.on_message(filters.incoming & filters.command([Command.SUB, f"{Command.SUB}@{BOT_USERNAME}"]) & is_auth)
async def sub_handler(client, message):
    if not message.from_user:
        return
    user_id = message.from_user.id
    reply = message.reply_to_message

    if reply and (reply.video or (reply.document and reply.document.mime_type and reply.document.mime_type.startswith("video/"))):
        subtitle_sessions[user_id] = {'video': reply}

        # Try to remove the video from the compression queue if it was automatically added
        removed = await remove_from_queue(reply.id)
        if removed:
            LOGGER.info(f"Removed video {reply.id} from compression queue for subtitle task")

        await message.reply_text("🎬 **Video saved for subtitle task.**\n\nNow please send the **subtitle file** (e.g., .srt, .ass, .vtt).")
    else:
        await message.reply_text("❌ **Please reply to a video message with /sub to start.**")

@app.on_message(filters.incoming & filters.document & is_auth, group=-2)
async def subtitle_file_handler(client, message):
    if not message.from_user:
        return
    user_id = message.from_user.id

    # Check if user is in a subtitle session and waiting for the sub file
    if user_id in subtitle_sessions and 'video' in subtitle_sessions[user_id] and 'sub' not in subtitle_sessions[user_id]:
        file_name = message.document.file_name or ""
        if file_name.lower().endswith(('.srt', '.ass', '.vtt')):
            subtitle_sessions[user_id]['sub'] = message

            await message.reply_text(
                "📝 **Subtitle file received.**\n\nChoose the type of subtitle you want to add:",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("Soft Sub", callback_data="sub_soft"),
                        InlineKeyboardButton("Hard Sub", callback_data="sub_hard")
                    ]
                ]),
                quote=True
            )
            # Stop other handlers from processing this document (like the automatic compression)
            message.stop_propagation()
