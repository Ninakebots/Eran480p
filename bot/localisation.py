from bot.get_cfg import get_config
from bot.config import Config

class Localisation:
    START_TEXT = Config.START_MESSAGE
   
    ABS_TEXT = " Please don't be selfish."
    
    FORMAT_SELECTION = "Select the desired format: <a href='{}'>file size might be approximate</a> \nIf you want to set custom thumbnail, send photo before or quickly after tapping on any of the below buttons.\nYou can use /deletethumbnail to delete the auto-generated thumbnail."
    
    
    DOWNLOAD_START = "Dᴏᴡɴʟᴏᴀᴅɪɴɢ...📥" 
    
    UPLOAD_START = "Uᴘʟᴏᴀᴅɪɴɢ...📤"
    
    COMPRESS_START = "Tʀʏɪɴɢ ᴛᴏ Eɴᴄᴏᴅᴇ...📀"
    
    RCHD_BOT_API_LIMIT = "size greater than maximum allowed size (50MB). Neverthless, trying to upload."
    
    RCHD_TG_API_LIMIT = "Downloaded in {} seconds.\nDetected File Size: {}\nSorry. But, I cannot upload files greater than 1.95GB due to Telegram API limitations."
    
    COMPRESS_SUCCESS = "✨ **Vɪᴅᴇᴏ Eɴᴄᴏᴅᴇᴅ Sᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ!** ✨\n\n<blockquote><b>📥 Dᴏᴡɴʟᴏᴀᴅ Tɪᴍᴇ:</b> {}\n<b>📀 Eɴᴄᴏᴅɪɴɢ Tɪᴍᴇ:</b> {}\n<b>📤 Uᴘʟᴏᴀᴅ Tɪᴍᴇ:</b> {}</blockquote>\n\n<b>𝖯𝗈𝗐𝖽𝖾𝗋𝖾𝖽 𝖡𝗒 @Team_Wine</b>"

    COMPRESS_PROGRESS = "<blockquote>⏳ ETA: {}\n🚀 Pʀᴏɢʀᴇꜱꜱ: {}%</blockquote>"

    SAVED_CUSTOM_THUMB_NAIL = "Custom video / file thumbnail saved. This image will be used in the video / file."
    
    DEL_ETED_CUSTOM_THUMB_NAIL = "Cᴜꜱᴛᴏᴍ Tʜᴜᴍʙɴᴀɪʟ Cʟᴇᴀʀᴇᴅ Sᴜᴄᴄᴇꜱꜰᴜʟʟʏ...✅"
    
    FF_MPEG_DEL_ETED_CUSTOM_MEDIA = "Mᴇᴅɪᴀ Cʟᴇᴀʀᴇᴅ Sᴜᴄᴄᴇꜱꜰᴜʟʟʏ...✅"
    
    SAVED_RECVD_DOC_FILE = "Dᴏᴡɴʟᴏᴀᴅᴇᴅ Sᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ...✅"
    
    CUSTOM_CAPTION_UL_FILE = " "
    
    NO_CUSTOM_THUMB_NAIL_FOUND = "Nᴏ Cᴜꜱᴛᴏᴍ Tʜᴜᴍʙɴᴀɪʟ Fᴏᴜɴᴅ...💔"
    
    NO_VOID_FORMAT_FOUND = "no-one gonna help you\n{}"
    
    USER_ADDED_TO_DB = "User <a href='tg://user?id={}'>{}</a> added to {} till {}."
    
    FF_MPEG_RO_BOT_STOR_AGE_ALREADY_EXISTS = "⚠️ Already one Process going on! ⚠️ \n\nCheck Live Status on Encoder Logs ."
    
    HELP_MESSAGE = Config.HELP_MESSAGE
    ABOUT_TEXT = Config.ABOUT_MESSAGE
    HELP_BUTTON = "Help 🛠"
    ABOUT_BUTTON = "About ℹ️"
    BACK_BUTTON = "Back 🔙"
    WRONG_MESSAGE = get_config(
        "STRINGS_WRONG_MESSAGE",
        "current CHAT ID: <code>{CHAT_ID}</code>"
    )
