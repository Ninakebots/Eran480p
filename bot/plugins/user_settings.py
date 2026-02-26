from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from bot.helper_funcs.menu_handler import menu_handler
from bot.helper_funcs.database import get_user_data, update_user_data
from bot.helper_funcs.utils import is_auth
import asyncio
import logging

active_sessions = {}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@Client.on_message(filters.command("us") & is_auth)
async def user_settings(client: Client, message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name

    # Capture context if it's a reply to a media file
    context = ""
    if message.reply_to_message:
        context = f"|{message.reply_to_message.id}"

    text, keyboard = await menu_handler.main_menu(user_id, username, context)
    await message.reply(text, reply_markup=keyboard)


async def wait_for_user_input(client: Client, user_id: int, chat_id: int, timeout: int = 60):
    future = asyncio.Future()

    if user_id in active_sessions:
        old_future = active_sessions[user_id].get("future")
        if old_future and not old_future.done():
            old_future.cancel()

    active_sessions[user_id] = {
        "future": future,
        "chat_id": chat_id,
        "timestamp": asyncio.get_event_loop().time(),
    }

    logger.info(f"Created session for user {user_id} in chat {chat_id}")

    try:
        result = await asyncio.wait_for(future, timeout=timeout)
        logger.info(f"Session completed for user {user_id}: {result[:50] if result else 'None'}...")
        return result
    except asyncio.TimeoutError:
        logger.info(f"Session timeout for user {user_id}")
        return None
    except asyncio.CancelledError:
        logger.info(f"Session cancelled for user {user_id}")
        return None
    finally:
        active_sessions.pop(user_id, None)


@Client.on_message(filters.private & filters.text)
async def handle_private_message(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id in active_sessions and active_sessions[user_id]["chat_id"] == message.chat.id:
        future = active_sessions[user_id]["future"]
        if not future.done():
            future.set_result(message.text)
            logger.info(f"Received input from user {user_id}: {message.text[:50]}...")


# --- Callback Data Helpers ---

def parse_cb_data(data):
    parts = data.split('|')
    base = parts[0]
    context = f"|{parts[1]}" if len(parts) > 1 else ""
    reply_to_id = int(parts[1]) if len(parts) > 1 else None
    return base, context, reply_to_id

# --- Menu Handlers ---

@Client.on_callback_query(filters.regex(r"^close_menu$"))
async def close_menu(client: Client, callback_query: CallbackQuery):
    await callback_query.message.delete()

@Client.on_callback_query(filters.regex(r"^main_menu"))
async def main_menu_handler(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username or callback_query.from_user.first_name
    _, context, _ = parse_cb_data(callback_query.data)
    
    text, keyboard = await menu_handler.main_menu(user_id, username, context)
    await callback_query.message.edit_text(text, reply_markup=keyboard)

@Client.on_callback_query(filters.regex(r"^util_menu"))
async def utility_menu_handler(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    _, context, _ = parse_cb_data(callback_query.data)
    text, keyboard = await menu_handler.utility_menu(user_id, context)
    await callback_query.message.edit_text(text, reply_markup=keyboard)

@Client.on_callback_query(filters.regex(r"^enc_menu"))
async def encoding_menu_handler(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    _, context, _ = parse_cb_data(callback_query.data)
    text, keyboard = await menu_handler.encoding_settings_menu(user_id, context)
    await callback_query.message.edit_text(text, reply_markup=keyboard)

# --- Encoding Settings Submenus ---

@Client.on_callback_query(filters.regex(r"^set_(codec|res|crf|pre|aud)"))
async def set_encoding_setting_handler(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    base, context, _ = parse_cb_data(callback_query.data)

    if base == "set_codec":
        text, keyboard = await menu_handler.set_codec_menu(user_id, context)
    elif base == "set_res":
        text, keyboard = await menu_handler.set_res_menu(user_id, context)
    elif base == "set_crf":
        text, keyboard = await menu_handler.set_crf_menu(user_id, context)
    elif base == "set_pre":
        text, keyboard = await menu_handler.set_pre_menu(user_id, context)
    elif base == "set_aud":
        text, keyboard = await menu_handler.set_aud_menu(user_id, context)

    await callback_query.message.edit_text(text, reply_markup=keyboard)

@Client.on_callback_query(filters.regex(r"^upd_(codec|res|crf|pre|aud)_"))
async def update_encoding_setting_handler(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    base, context, _ = parse_cb_data(callback_query.data)

    # Extract key and value from upd_key_value
    parts = base.split('_')
    key_short = parts[1]
    value = parts[2]

    key_map = {
        'codec': 'codec',
        'res': 'resolution',
        'crf': 'crf',
        'pre': 'preset',
        'aud': 'audio_b'
    }
    key = key_map.get(key_short)

    if key:
        await update_user_data(user_id, {key: value})
        await callback_query.answer(f"✅ {key} updated to {value}")

    # Go back to encoding menu
    text, keyboard = await menu_handler.encoding_settings_menu(user_id, context)
    await callback_query.message.edit_text(text, reply_markup=keyboard)

# --- Media Tools Handlers ---

@Client.on_callback_query(filters.regex(r"^(ext_aud|rem_aud|add_aud|trim_vid|soft_sub|hard_sub|rem_sub|m_info|sav_thumb|del_thumb)"))
async def media_tools_callback_handler(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    base, context, reply_to_id = parse_cb_data(callback_query.data)

    if not reply_to_id and base not in ["del_thumb"]:
        return await callback_query.answer("❌ Please reply to a media file with /us to use this tool.", show_alert=True)

    # Fetch the original message to get the replied media
    try:
        if reply_to_id:
            media_message = await client.get_messages(callback_query.message.chat.id, reply_to_id)
        else:
            media_message = None
    except Exception as e:
        return await callback_query.answer(f"❌ Could not find the original media: {e}", show_alert=True)

    from bot.helper_funcs.utils import add_to_queue

    if base == "ext_aud":
        if not (media_message.video or media_message.document):
            return await callback_query.answer("❌ This is not a video file.", show_alert=True)
        await add_to_queue(media_message, "extract_audio")
        await callback_query.answer("⏰ Audio extraction added to queue.")

    elif base == "rem_aud":
        if not (media_message.video or media_message.document):
            return await callback_query.answer("❌ This is not a video file.", show_alert=True)
        await add_to_queue(media_message, "remove_audio")
        await callback_query.answer("⏰ Remove audio added to queue.")

    elif base == "add_aud":
        if not (media_message.audio or media_message.document):
            return await callback_query.answer("❌ Please reply to an audio file which is itself a reply to a video file, then send /us to the audio file.", show_alert=True)

        video_message = None
        if media_message.reply_to_message and (media_message.reply_to_message.video or media_message.reply_to_message.document):
            video_message = media_message.reply_to_message

        if not video_message:
            return await callback_query.answer("❌ This audio file is not a reply to a video file.", show_alert=True)

        await add_to_queue(video_message, "add_audio", options={'audio_message': media_message})
        await callback_query.answer("⏰ Add audio added to queue.")

    elif base == "trim_vid":
        if not (media_message.video or media_message.document):
            return await callback_query.answer("❌ This is not a video file.", show_alert=True)

        await callback_query.message.delete()

        # We need start and end time. Ask user.
        ask_start = await client.send_message(callback_query.message.chat.id, "✂️ **Trimming**\nSend the start time (e.g., `00:01:00`):", reply_to_message_id=media_message.id)
        start_time = await wait_for_user_input(client, user_id, callback_query.message.chat.id)
        if not start_time: return await ask_start.edit_text("❌ Timeout.")

        ask_end = await client.send_message(callback_query.message.chat.id, "Send the end time (e.g., `00:02:30`):", reply_to_message_id=media_message.id)
        end_time = await wait_for_user_input(client, user_id, callback_query.message.chat.id)
        if not end_time: return await ask_end.edit_text("❌ Timeout.")

        await add_to_queue(media_message, "trim", options={'start_time': start_time, 'end_time': end_time})
        await client.send_message(callback_query.message.chat.id, f"⏰ Trim task ({start_time} - {end_time}) added to queue.")

    elif base == "soft_sub":
        if not media_message.document:
            return await callback_query.answer("❌ This is not a subtitle file.", show_alert=True)

        video_message = None
        if media_message.reply_to_message and (media_message.reply_to_message.video or media_message.reply_to_message.document):
            video_message = media_message.reply_to_message

        if not video_message:
            return await callback_query.answer("❌ This subtitle file is not a reply to a video file.", show_alert=True)

        await add_to_queue(video_message, "add_soft_sub", options={'sub_message': media_message})
        await callback_query.answer("⏰ Soft-sub added to queue.")

    elif base == "hard_sub":
        if not media_message.document:
            return await callback_query.answer("❌ This is not a subtitle file.", show_alert=True)

        video_message = None
        if media_message.reply_to_message and (media_message.reply_to_message.video or media_message.reply_to_message.document):
            video_message = media_message.reply_to_message

        if not video_message:
            return await callback_query.answer("❌ This subtitle file is not a reply to a video file.", show_alert=True)

        await add_to_queue(video_message, "add_hard_sub", options={'sub_message': media_message})
        await callback_query.answer("⏰ Hard-sub added to queue.")

    elif base == "rem_sub":
        if not (media_message.video or media_message.document):
            return await callback_query.answer("❌ This is not a video file.", show_alert=True)
        await add_to_queue(media_message, "remove_sub")
        await callback_query.answer("⏰ Remove sub added to queue.")

    elif base == "m_info":
        if not (media_message.video or media_message.document):
            return await callback_query.answer("❌ This is not a video file.", show_alert=True)
        await add_to_queue(media_message, "mediainfo")
        await callback_query.answer("⏰ MediaInfo added to queue.")

    elif base == "sav_thumb":
        if not media_message.photo:
            return await callback_query.answer("❌ Please reply to a photo with /us to save it.", show_alert=True)

        thumb_dir = "thumbnails"
        os.makedirs(thumb_dir, exist_ok=True)
        thumb_path = os.path.join(thumb_dir, f"{user_id}.jpg")

        await client.download_media(message=media_message.photo, file_name=thumb_path)
        await callback_query.answer("✅ Custom thumbnail saved.")

    elif base == "del_thumb":
        thumb_path = os.path.join("thumbnails", f"{user_id}.jpg")
        if os.path.exists(thumb_path):
            os.remove(thumb_path)
            await callback_query.answer("✅ Custom thumbnail deleted.")
        else:
            await callback_query.answer("❌ No custom thumbnail found.", show_alert=True)


