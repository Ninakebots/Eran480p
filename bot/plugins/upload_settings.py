from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from bot import app, BOT_USERNAME
from bot.commands import Command
from bot.helper_funcs.utils import is_auth
from bot.helper_funcs.database import update_user_data, get_user_data
import logging

LOGGER = logging.getLogger(__name__)

@app.on_message(filters.command([Command.SETUPLOAD, f"{Command.SETUPLOAD}@{BOT_USERNAME}"]) & is_auth)
async def setupload_command_handler(client: Client, message: Message):
    user_id = message.from_user.id
    user_data = await get_user_data(user_id)
    current_dest = user_data.get("upload_destination", "Telegram")

    text = f"📤 **Upload Settings**\n\nCᴜʀʀᴇɴᴛ Dᴇꜱᴛɪɴᴀᴛɪᴏɴ: `{current_dest.capitalize()}`\n\nSᴇʟᴇᴄᴛ ᴡʜᴇʀᴇ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴜᴘʟᴏᴀᴅ ʏᴏᴜʀ ꜰɪʟᴇꜱ:"

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Telegram", callback_data="set_upload_tg"),
            InlineKeyboardButton("Gofile", callback_data="set_upload_gofile")
        ],
        [InlineKeyboardButton("❌ Close", callback_data="close_menu")]
    ])

    await message.reply_text(text, reply_markup=keyboard)

@app.on_callback_query(filters.regex(r"^set_upload_(tg|gofile)$"))
async def set_upload_callback_handler(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data

    dest = "telegram" if data == "set_upload_tg" else "gofile"

    await update_user_data(user_id, {"upload_destination": dest})

    await callback_query.answer(f"✅ Upload destination set to {dest.capitalize()}", show_alert=True)

    # Update the message
    text = f"📤 **Upload Settings**\n\nCᴜʀʀᴇɴᴛ Dᴇꜱᴛɪɴᴀᴛɪᴏɴ: `{dest.capitalize()}`\n\nSᴇʟᴇᴄᴛ ᴡʜᴇʀᴇ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴜᴘʟᴏᴀᴅ ʏᴏᴜʀ ꜰɪʟᴇꜱ:"
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Telegram", callback_data="set_upload_tg"),
            InlineKeyboardButton("Gofile", callback_data="set_upload_gofile")
        ],
        [InlineKeyboardButton("❌ Close", callback_data="close_menu")]
    ])

    try:
        await callback_query.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        pass
