from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from bot.helper_funcs.menu_handler import menu_handler
from bot.helper_funcs.database import get_user_data, update_user_data
from bot.helper_funcs.utils import is_auth, is_personal_auth
from bot import app, AUTH_USERS
import asyncio
import logging
import os

active_sessions = {}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.on_message(filters.command("settings") & is_auth)
async def personal_settings(client, message: Message):
    if not message.from_user:
        return
    user_id = message.from_user.id
    is_admin = user_id in AUTH_USERS and user_id > 0
    text, keyboard = await menu_handler.global_settings_menu("480p", is_admin)
    await message.reply(text, reply_markup=keyboard)


@app.on_callback_query(filters.regex(r"^view_global_(480p|720p|1080p)"))
async def view_global_settings(client, callback_query: CallbackQuery):
    if not callback_query.from_user:
        return
    user_id = callback_query.from_user.id
    res_key = callback_query.data.split('_')[-1]
    is_admin = user_id in AUTH_USERS and user_id > 0
    text, keyboard = await menu_handler.global_settings_menu(res_key, is_admin)
    await callback_query.message.edit_text(text, reply_markup=keyboard)


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


@app.on_message(filters.private & filters.text)
async def handle_private_message(client, message: Message):
    if not message.from_user:
        return
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
    context = "|".join(parts[1:])
    if context:
        context = "|" + context

    reply_to_id = None
    if len(parts) > 1 and parts[1].isdigit():
        reply_to_id = int(parts[1])

    return base, context, reply_to_id

# --- Menu Handlers ---

@app.on_callback_query(filters.regex(r"^close_menu$"))
async def close_menu(client, callback_query: CallbackQuery):
    await callback_query.message.delete()

@app.on_callback_query(filters.regex(r"^(settings_menu|enc_menu)"))
async def settings_menu_handler(client, callback_query: CallbackQuery):
    if not callback_query.from_user:
        return
    user_id = callback_query.from_user.id

    # Check for personal auth
    if user_id not in AUTH_USERS or user_id <= 0:
        return await callback_query.answer("❌ You are not authorized to change these settings.", show_alert=True)

    _, context, _ = parse_cb_data(callback_query.data)
    text, keyboard = await menu_handler.settings_menu(user_id, context)
    await callback_query.message.edit_text(text, reply_markup=keyboard)

# --- Encoding Settings Submenus ---

@app.on_callback_query(filters.regex(r"^set_(codec|res|crf|pre|aud)"))
async def set_encoding_setting_handler(client, callback_query: CallbackQuery):
    if not callback_query.from_user:
        return
    user_id = callback_query.from_user.id
    base, context, _ = parse_cb_data(callback_query.data)

    # Check for personal auth
    if user_id not in AUTH_USERS or user_id <= 0:
        return await callback_query.answer("❌ You are not authorized to change these settings.", show_alert=True)

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

@app.on_callback_query(filters.regex(r"^upd_(codec|res|crf|pre|aud)_"))
async def update_encoding_setting_handler(client, callback_query: CallbackQuery):
    if not callback_query.from_user:
        return
    user_id = callback_query.from_user.id
    base, context, reply_to_id = parse_cb_data(callback_query.data)

    # Extract key and value from upd_key_value
    parts = base.split('_')
    key_short = parts[1]
    value = parts[2]

    # Check for personal auth
    if user_id not in AUTH_USERS or user_id <= 0:
        return await callback_query.answer("❌ You are not authorized to change these settings.", show_alert=True)

    key_map = {
        'codec': 'codec',
        'res': 'resolution',
        'crf': 'crf',
        'pre': 'preset',
        'aud': 'audio_b'
    }
    key = key_map.get(key_short)

    if key:
        if "|global|" in context:
            res_key = context.split('|')[-1]
            from bot.helper_funcs.database import get_global_settings, update_global_settings
            g = await get_global_settings(res_key)
            g[key] = value
            await update_global_settings(res_key, g)
            await callback_query.answer(f"✅ Global {res_key} {key} updated to {value}")
        else:
            if key == "resolution" and value == "All":
                await update_user_data(user_id, {key: value})
                if reply_to_id:
                    # Triggers 3 encoding tasks immediately
                    from bot.helper_funcs.utils import add_to_queue
                    try:
                        media_message = await client.get_messages(callback_query.message.chat.id, reply_to_id)
                        await add_to_queue(media_message, "480p")
                        await add_to_queue(media_message, "720p")
                        await add_to_queue(media_message, "1080p")
                        await callback_query.answer("⏰ Default set to 'All' and added all 3 tasks to queue!", show_alert=True)
                    except Exception as e:
                        await callback_query.answer(f"❌ Error queuing tasks: {e}", show_alert=True)
                else:
                    await callback_query.answer("✅ 'All' selected as default resolution.")
            else:
                await update_user_data(user_id, {key: value})
                await callback_query.answer(f"✅ {key} updated to {value}")

    # Route back to appropriate menu
    if key_short == "res" and "global" not in context.split('|'):
        # Route back to media settings if context is empty (general settings)
        if not context:
            from bot.plugins.utility_handlers import set_media_callback_handler
            callback_query.data = "back_to_media"
            await set_media_callback_handler(client, callback_query)
        else:
            await callback_query.answer(f"✅ Default resolution set to {value}")
            await callback_query.message.delete()
    else:
        text, keyboard = await menu_handler.settings_menu(user_id, context)
        await callback_query.message.edit_text(text, reply_markup=keyboard)


