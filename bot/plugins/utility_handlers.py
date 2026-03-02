import os
import asyncio
import logging
import speedtest
import subprocess
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from bot import BOT_USERNAME, data, app, AUTH_USERS
from bot.commands import Command
from bot.helper_funcs.utils import sysinfo, is_auth, hbs
from bot.helper_funcs.database import get_user_data, update_user_data
from bot.localisation import Localisation

LOGGER = logging.getLogger(__name__)

@app.on_message(filters.incoming & filters.command([Command.LIST, f"{Command.LIST}@{BOT_USERNAME}"]) & is_auth)
async def list_handler(client, message):
    if not data:
        return await message.reply_text("📚 Queue is empty.")

    text = "📚 **Active Queue:**\n\n"
    for i, task in enumerate(data):
        task_type = task.get('task_type')
        msg = task.get('message')
        text += f"{i+1}. **{task_type}** - ID: `{task.get('id')}`\n"

    await message.reply_text(text)

@app.on_message(filters.incoming & filters.command([Command.SYSINFO, f"{Command.SYSINFO}@{BOT_USERNAME}"]) & is_auth)
async def sysinfo_handler(client, message):
    await sysinfo(message)

@app.on_message(filters.incoming & filters.command([Command.SPEEDTEST, f"{Command.SPEEDTEST}@{BOT_USERNAME}"]) & is_auth)
async def speedtest_handler(client, message):
    sent = await message.reply_text("🏎 **Running speed test...**")
    try:
        st = speedtest.Speedtest(secure=True)
        await asyncio.to_thread(st.get_best_server)
        await asyncio.to_thread(st.download)
        await asyncio.to_thread(st.upload)
        res = st.results.dict()

        isp = res.get('client', {}).get('isp', 'Unknown')
        server = res.get('server', {}).get('sponsor', 'Unknown')
        country = res.get('server', {}).get('country', 'Unknown')
        ping = res.get('ping', 0)
        download = res.get('download', 0)
        upload = res.get('upload', 0)

        text = (
            f"🏎 **Speed Test Results:**\n\n"
            f"🌐 **ISP:** `{isp}`\n"
            f"📡 **Server:** `{server}, {country}`\n\n"
            f"⬇️ **Download:** `{hbs(download / 8)}/s`\n"
            f"⬆️ **Upload:** `{hbs(upload / 8)}/s`\n"
            f"🏓 **Ping:** `{ping} ms`"
        )
        await sent.edit_text(text)
    except Exception as e:
        LOGGER.error(f"Speedtest error: {e}")
        # Fallback to simple speedtest-cli if available
        try:
            output = await asyncio.to_thread(
                lambda: subprocess.check_output(['speedtest-cli', '--simple'], stderr=subprocess.STDOUT).decode()
            )
            await sent.edit_text(f"🏎 **Speed Test Results (Fallback):**\n\n`{output}`")
        except Exception as err:
            await sent.edit_text(f"❌ **Speed test failed.**\n\n**Error:** `{e}`\n**Fallback Error:** `{err}`")

@app.on_message(filters.incoming & filters.command([Command.PING, f"{Command.PING}@{BOT_USERNAME}"]) & is_auth)
async def ping_handler(client, message):
    start_time = time.time()
    sent = await message.reply_text("🏓 **Pinging...**")
    end_time = time.time()
    latency = (end_time - start_time) * 1000
    await sent.edit_text(f"🏓 **Pong!**\nLatency: `{latency:.2f} ms`")

@app.on_message(filters.incoming & filters.command([Command.SETUPLOAD, f"{Command.SETUPLOAD}@{BOT_USERNAME}"]) & is_personal_auth)
async def setupload_handler(client, message):
    args = message.text.split(" ")
    if len(args) < 2:
        return await message.reply_text(
            "📍 **Upload Settings**\n\n"
            "Usage: `/setupload [destination]`\n\n"
            "**Destinations:**\n"
            "• `pm` - Upload to Private Message\n"
            "• `chat` - Upload to current chat\n"
            "• `ID` - Upload to specific Chat ID (e.g., `-100...`)"
        )

    dest = args[1].lower()
    user_id = message.from_user.id

    if dest in ["pm", "chat"]:
        await update_user_data(user_id, {"upload_destination": dest})
        await message.reply_text(f"✅ Upload destination set to: `{dest.upper()}`")
    else:
        # Try to validate if it's a valid ID
        try:
            chat_id = int(dest)
            await update_user_data(user_id, {"upload_destination": chat_id})
            await message.reply_text(f"✅ Upload destination set to Chat ID: `{chat_id}`")
        except ValueError:
            await message.reply_text("❌ Invalid destination. Use `pm`, `chat` or a valid numeric `ID`.")

@app.on_message(filters.incoming & filters.command([Command.SETMEDIA, f"{Command.SETMEDIA}@{BOT_USERNAME}"]) & is_personal_auth)
async def setmedia_handler(client, message):
    user_id = message.from_user.id
    user_data = await get_user_data(user_id)
    current_media = user_data.get("upload_as", "video")
    res = user_data.get("resolution", "720p")

    text = (
        f"📂 **Media Settings**\n\n"
        f"Cᴜʀʀᴇɴᴛ Pʀᴇꜰᴇʀᴇɴᴄᴇ: `{current_media.capitalize()}`\n"
        f"Cᴜʀʀᴇɴᴛ Rᴇsᴏʟᴜᴛɪᴏɴ: `{res}`\n\n"
        "Sᴇʟᴇᴄᴛ ᴀ sᴇᴛᴛɪɴɢ ᴛᴏ ᴄʜᴀɴɢᴇ ɪᴛ:"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Video", callback_data="set_media_video"),
            InlineKeyboardButton("Document", callback_data="set_media_document")
        ],
        [InlineKeyboardButton("🎬 Resolution", callback_data="set_res")],
        [InlineKeyboardButton("❌ Close", callback_data="close_menu")]
    ])

    await message.reply_text(text, reply_markup=keyboard)

@app.on_callback_query(filters.regex(r"^(set_media_(video|document)|back_to_media)$"))
async def set_media_callback_handler(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id not in AUTH_USERS or user_id <= 0:
        return await callback_query.answer("❌ You are not authorized to change these settings.", show_alert=True)

    data = callback_query.data

    if data.startswith("set_media_"):
        media_type = "video" if data == "set_media_video" else "document"
        await update_user_data(user_id, {"upload_as": media_type})
        await callback_query.answer(f"✅ Upload preference set to {media_type.capitalize()}", show_alert=True)

    user_data = await get_user_data(user_id)
    current_media = user_data.get("upload_as", "video")
    res = user_data.get("resolution", "720p")

    text = (
        f"📂 **Media Settings**\n\n"
        f"Cᴜʀʀᴇɴᴛ Pʀᴇꜰᴇʀᴇɴᴄᴇ: `{current_media.capitalize()}`\n"
        f"Cᴜʀʀᴇɴᴛ Rᴇsᴏʟᴜᴛɪᴏɴ: `{res}`\n\n"
        "Sᴇʟᴇᴄᴛ ᴀ sᴇᴛᴛɪɴɢ ᴛᴏ ᴄʜᴀɴɢᴇ ɪᴛ:"
    )
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Video", callback_data="set_media_video"),
            InlineKeyboardButton("Document", callback_data="set_media_document")
        ],
        [InlineKeyboardButton("🎬 Resolution", callback_data="set_res")],
        [InlineKeyboardButton("❌ Close", callback_data="close_menu")]
    ])
    try:
        await callback_query.message.edit_text(text, reply_markup=keyboard)
    except:
        pass

@app.on_message(filters.incoming & filters.command([Command.CANCEL, f"{Command.CANCEL}@{BOT_USERNAME}"]) & is_auth)
async def cancel_handler(client, message):
    args = message.text.split(" ")
    if len(args) > 1:
        try:
            task_id = int(args[1])
            found = False
            for i, task in enumerate(data):
                if task.get('id') == task_id:
                    if i == 0:
                        await message.reply_text("❌ Cannot cancel active task with ID. Use /cancel without arguments for active task.")
                    else:
                        data.pop(i)
                        await message.reply_text(f"✅ Task with ID `{task_id}` removed from queue.")
                    found = True
                    break
            if not found:
                # Try index if not ID
                if 1 <= task_id <= len(data):
                    if task_id == 1:
                        await message.reply_text("❌ Cannot cancel active task with Index. Use /cancel without arguments for active task.")
                    else:
                        data.pop(task_id - 1)
                        await message.reply_text(f"✅ Task at index `{task_id}` removed from queue.")
                else:
                    await message.reply_text(f"❌ No task found with ID or Index `{task_id}`.")
        except ValueError:
            await message.reply_text("❌ Invalid task ID/Index format.")
    else:
        from bot.plugins.incoming_message_fn import incoming_cancel_message_f
        await incoming_cancel_message_f(client, message)

