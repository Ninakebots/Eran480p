from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from bot.helper_funcs.menu_handler import menu_handler
from bot.helper_funcs.database import get_user_data, update_user_data
from bot import AUTH_USERS
import asyncio
import logging

active_sessions = {}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@Client.on_message(filters.command("us"))
async def user_settings(client: Client, message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    username = message.from_user.username or message.from_user.first_name

    from bot.config import AUTH_CHATS
    if (
        message.chat.type != "private"
        and chat_id not in AUTH_CHATS
        and user_id not in AUTH_USERS
    ):
        return await message.reply("🚫 You are not authorized to use this command.")

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


@Client.on_callback_query(filters.regex(r"^watermark_menu$"))
async def watermark_menu_handler(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username or callback_query.from_user.first_name

    text, keyboard = await menu_handler.watermark_menu(user_id, username)
    await callback_query.message.edit_text(text, reply_markup=keyboard)


@Client.on_callback_query(filters.regex(r"^set_watermark_url$"))
async def set_watermark_url_handler(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username or callback_query.from_user.first_name

    user_data = await get_user_data(user_id)
    current_watermark = user_data.get("watermark_url", "None set")

    text = (
        f"🖋 **Set Watermark URL for** `{username}`\n\n"
        f"**Current Watermark URL:** `{current_watermark}`\n\n"
        "Please send a new URL (must be a direct link to PNG/JPG image):"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Cancel", callback_data="watermark_menu")]
    ])

    await callback_query.message.edit_text(text, reply_markup=keyboard)

    input_text = await wait_for_user_input(client, user_id, callback_query.message.chat.id)
    if input_text:
        if input_text.startswith(("http://", "https://")) and input_text.lower().endswith((".png", ".jpg", ".jpeg")):
            await update_user_data(user_id, {"watermark_url": input_text})
            
            # Show success and return to watermark menu
            text, keyboard = await menu_handler.watermark_menu(user_id, username)
            await callback_query.message.edit_text(
                f"✅ **Watermark URL updated successfully!**\n\n{text}",
                reply_markup=keyboard
            )
        else:
            # Show error and return to watermark menu
            text, keyboard = await menu_handler.watermark_menu(user_id, username)
            await callback_query.message.edit_text(
                f"❌ **Invalid URL!** Must be a direct link to a PNG/JPG image.\n\n{text}",
                reply_markup=keyboard
            )
    else:
        # Timeout - return to watermark menu
        text, keyboard = await menu_handler.watermark_menu(user_id, username)
        await callback_query.message.edit_text(
            f"⏰ **Input timed out.**\n\n{text}",
            reply_markup=keyboard
        )


@Client.on_callback_query(filters.regex(r"^opacity_menu$"))
async def opacity_menu_handler(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    text, keyboard = await menu_handler.opacity_menu(user_id)
    await callback_query.message.edit_text(text, reply_markup=keyboard)


@Client.on_callback_query(filters.regex(r"^opacity_(\d+)$"))
async def opacity_set_handler(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username or callback_query.from_user.first_name
    opacity = int(callback_query.data.split("_")[1])
    
    await update_user_data(user_id, {"opacity": opacity})
    
    text, keyboard = await menu_handler.watermark_menu(user_id, username)
    await callback_query.message.edit_text(text, reply_markup=keyboard)
    await callback_query.answer(f"✅ Opacity set to {opacity}%")


@Client.on_callback_query(filters.regex(r"^position_menu$"))
async def position_menu_handler(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    text, keyboard = await menu_handler.position_menu(user_id)
    await callback_query.message.edit_text(text, reply_markup=keyboard)


@Client.on_callback_query(filters.regex(r"^pos_(.+)$"))
async def position_set_handler(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username or callback_query.from_user.first_name
    position = callback_query.data.replace("pos_", "")
    
    await update_user_data(user_id, {"position": position})
    
    text, keyboard = await menu_handler.watermark_menu(user_id, username)
    await callback_query.message.edit_text(text, reply_markup=keyboard)
    await callback_query.answer("✅ Position updated")


@Client.on_callback_query(filters.regex(r"^size_menu$"))
async def size_menu_handler(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    text, keyboard = await menu_handler.size_menu(user_id)
    await callback_query.message.edit_text(text, reply_markup=keyboard)


@Client.on_callback_query(filters.regex(r"^size_(\d+)$"))
async def size_set_handler(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username or callback_query.from_user.first_name
    size = int(callback_query.data.split("_")[1])
    
    await update_user_data(user_id, {"size": size})
    
    text, keyboard = await menu_handler.watermark_menu(user_id, username)
    await callback_query.message.edit_text(text, reply_markup=keyboard)
    await callback_query.answer(f"✅ Size set to {size}%")
