from bot.helper_funcs.utils import on_task_complete, add_task, is_auth
from bot.helper_funcs.database import db
from bot.localisation import Localisation
from bot import AUTH_USERS, DOWNLOAD_LOCATION, data, pid_list, subtitle_sessions
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
import logging
import os, signal
import json
import shutil

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
LOGGER = logging.getLogger(__name__)

async def button(bot, update: CallbackQuery):
    cb_data = update.data
    user_id = update.from_user.id
    username = update.from_user.username or update.from_user.first_name
    try:
        g = await AdminCheck(bot, update.message.chat.id, update.from_user.id)
    except:
        g = False

    if cb_data == "help":
        await update.message.edit_text(
            text=Localisation.HELP_MESSAGE,
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton(Localisation.BACK_BUTTON, callback_data="start_back")]
                ]
            )
        )
        return

    elif cb_data == "about":
        await update.message.edit_text(
            text=Localisation.ABOUT_TEXT,
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton(Localisation.BACK_BUTTON, callback_data="start_back")]
                ]
            )
        )
        return

    elif cb_data == "start_back":
        await update.message.edit_text(
            text=Localisation.START_TEXT,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton('𝖳𝖾𝖺𝗆 𝖶𝗂𝗇𝖾', url='https://t.me/Team_Wine')
                    ],
                    [
                        InlineKeyboardButton(Localisation.HELP_BUTTON, callback_data="help"),
                        InlineKeyboardButton(Localisation.ABOUT_BUTTON, callback_data="about")
                    ]
                ]
            )
        )
        return

    if cb_data.startswith("cancel_"):
        pid = int(cb_data.split("_")[1])
        if pid in pid_list:
            try:
                os.kill(pid, signal.SIGTERM)
                pid_list.remove(pid)
                await update.answer("❌ Process cancelled!")
                await update.message.delete()
            except ProcessLookupError:
                await update.answer("Process already terminated")
                if pid in pid_list:
                    pid_list.remove(pid)
            except Exception as e:
                await update.answer("Failed to cancel process")
                LOGGER.error(f"Error cancelling process: {e}")
        else:
            await update.answer("Process not found")

    if (update.from_user and update.message.reply_to_message and update.message.reply_to_message.from_user and (update.from_user.id == update.message.reply_to_message.from_user.id)) or g:
        if cb_data == "fuckingdo":
            # Check if user is an admin or authorized in DB
            is_authorized = await is_auth(bot, update)
            if is_authorized:
                status = DOWNLOAD_LOCATION + "/status.json"
                with open(status, 'r+') as f:
                    statusMsg = json.load(f)
                    statusMsg['running'] = False
                    f.seek(0)
                    json.dump(statusMsg, f, indent=2)
                    if 'pid' in statusMsg.keys():
                        try:
                            os.kill(statusMsg["pid"], signal.SIGTERM)
                            os.kill(pid_list[0], signal.SIGTERM)
                            del pid_list[0]
                            os.system("rm -rf downloads/*")
                            await bot.delete_messages(update.message.chat.id, statusMsg["message"])
                        except Exception:
                            pass
            else:
                try:
                    await update.message.edit_text("Yᴏᴜ ᴀʀᴇ Nᴏᴛ Aʟʟᴏᴡᴇᴅ ᴛᴏ ᴅᴏ Tʜᴀᴛ 🤭")
                except:
                    pass
        elif cb_data == "fuckoff":
            try:
                await update.message.edit_text("Oᴋᴀʏ! Fɪɴᴇ ☠️")
            except:
                pass

    if cb_data.startswith("sub_"):
        if user_id in subtitle_sessions:
            sub_type = cb_data.split("_")[1]
            task_type = f"add_{sub_type}_sub"
            video_message = subtitle_sessions[user_id]['video']
            sub_message = subtitle_sessions[user_id]['sub']

            await update.message.edit_text(f"⏰ Added **{sub_type} sub** task to queue...")
            from bot.helper_funcs.utils import add_to_queue
            await add_to_queue(video_message, task_type, options={'sub_message': sub_message})

            # Clear session
            del subtitle_sessions[user_id]
        else:
            await update.answer("❌ Session expired or not found. Please start over with /sub.", show_alert=True)
            await update.message.delete()

async def AdminCheck(bot, chat_id, user_id):
    try:
        chat_member = await bot.get_chat_member(chat_id, user_id)
        return chat_member.status in ["administrator", "creator"]
    except:
        return False
