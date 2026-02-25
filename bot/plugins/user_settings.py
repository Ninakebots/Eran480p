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

    text, keyboard = await menu_handler.main_menu(user_id, username)
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


# Callback query handlers for user settings
@Client.on_callback_query(filters.regex(r"^close_menu$"))
async def close_menu(client: Client, callback_query: CallbackQuery):
    await callback_query.message.delete()


@Client.on_callback_query(filters.regex(r"^main_menu$"))
async def main_menu_handler(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username or callback_query.from_user.first_name
    
    text, keyboard = await menu_handler.main_menu(user_id, username)
    await callback_query.message.edit_text(text, reply_markup=keyboard)


@Client.on_callback_query(filters.regex(r"^utility_menu$"))
async def utility_menu_handler(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    text, keyboard = await menu_handler.utility_menu(user_id)
    await callback_query.message.edit_text(text, reply_markup=keyboard)


@Client.on_callback_query(filters.regex(r"^util_(merge|audio|sub)$"))
async def util_info_handler(client: Client, callback_query: CallbackQuery):
    tool = callback_query.data.split("_")[1]
    if tool == "merge":
        msg = "🎬 **Merge Videos**\n\n1. Send `/merge` to start a session.\n2. Send or reply with videos you want to merge.\n3. Send `/done` to start the merging process."
    elif tool == "audio":
        msg = "🎵 **Add Audio**\n\n1. Reply to a video with the audio file.\n2. Reply to that audio file with `/addaudio`."
    elif tool == "sub":
        msg = "📝 **Add Subtitles**\n\n1. Reply to a video with the subtitle file (.srt/.ass).\n2. Reply to that subtitle file with `/sub` (soft) or `/hsub` (hard)."

    await callback_query.answer(msg, show_alert=True)


