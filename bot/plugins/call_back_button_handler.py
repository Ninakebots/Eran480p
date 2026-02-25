from bot.helper_funcs.utils import on_task_complete, add_task, is_auth
from bot.helper_funcs.database import db
from bot.localisation import Localisation
from bot import AUTH_USERS, DOWNLOAD_LOCATION, LOG_CHANNEL, data, pid_list
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
import datetime
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

    if (update.from_user.id == update.message.reply_to_message.from_user.id) or g:
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
                chat_id = LOG_CHANNEL
                utc_now = datetime.datetime.utcnow()
                ist_now = utc_now + datetime.timedelta(hours=5, minutes=30)
                ist = ist_now.strftime("%d/%m/%Y, %H:%M:%S")
                bst_now = utc_now + datetime.timedelta(hours=6)
                bst = bst_now.strftime("%d/%m/%Y, %H:%M:%S")
                now = f"{ist} (GMT+05:30)\n{bst} (GMT+06:00)"
                await bot.send_message(chat_id, "**𝙻𝚊𝚜𝚝 𝙿𝚛𝚘𝚌𝚎𝚜𝚜 𝙲𝚊𝚗𝚌𝚎𝚕𝚕𝚎𝚍.\n.....𝙱𝚘𝚝 𝚒𝚜 𝙵𝚛𝚎𝚎 𝙽𝚘𝚠.....🥀**")
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

async def AdminCheck(bot, chat_id, user_id):
    try:
        chat_member = await bot.get_chat_member(chat_id, user_id)
        return chat_member.status in ["administrator", "creator"]
    except:
        return False
