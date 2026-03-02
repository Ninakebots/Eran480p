from bot.get_cfg import get_config
from bot.config import Config
from bot.helper_funcs.utils import style_text

class Localisation:
    START_TEXT = style_text(Config.START_MESSAGE)
   
    ABS_TEXT = style_text(" Please don't be selfish.")
    
    FORMAT_SELECTION = style_text("Select the desired format: <a href='{}'>file size might be approximate</a> \nIf you want to set custom thumbnail, send photo before or quickly after tapping on any of the below buttons.\nYou can use /deletethumbnail to delete the auto-generated thumbnail.")
    
    
    DOWNLOAD_START = style_text("Downloading...📥")
    
    UPLOAD_START = style_text("Uploading...📤")
    
    COMPRESS_START = style_text("Trying to Encode...📀")
    
    RCHD_BOT_API_LIMIT = style_text("size greater than maximum allowed size (50MB). Neverthless, trying to upload.")
    
    RCHD_TG_API_LIMIT = style_text("Downloaded in {} seconds.\nDetected File Size: {}\nSorry. But, I cannot upload files greater than 1.95GB due to Telegram API limitations.")
    
    COMPRESS_SUCCESS = "✨ **" + style_text("Video Encoded Successfully!") + "** ✨\n\n<blockquote><b>📥 " + style_text("Download Time:") + "</b> {}\n<b>📀 " + style_text("Encoding Time:") + "</b> {}\n<b>📤 " + style_text("Upload Time:") + "</b> {}</blockquote>\n\n<b>" + style_text("Powered By @Team_Wine") + "</b>"

    COMPRESS_PROGRESS = "<blockquote>⏳ " + style_text("ETA:") + " {}\n🚀 " + style_text("Progress:") + " {}%</blockquote>"

    SAVED_CUSTOM_THUMB_NAIL = style_text("Custom video / file thumbnail saved. This image will be used in the video / file.")
    
    DEL_ETED_CUSTOM_THUMB_NAIL = style_text("Custom Thumbnail Cleared Successfully...✅")
    
    FF_MPEG_DEL_ETED_CUSTOM_MEDIA = style_text("Media Cleared Successfully...✅")
    
    SAVED_RECVD_DOC_FILE = style_text("Downloaded Successfully...✅")
    
    CUSTOM_CAPTION_UL_FILE = " "
    
    NO_CUSTOM_THUMB_NAIL_FOUND = style_text("No Custom Thumbnail Found...💔")
    
    NO_VOID_FORMAT_FOUND = style_text("no-one gonna help you\n{}")
    
    USER_ADDED_TO_DB = style_text("User <a href='tg://user?id={}'>{}</a> added to {} till {}.")
    
    FF_MPEG_RO_BOT_STOR_AGE_ALREADY_EXISTS = "⚠️ " + style_text("Already one Process going on!") + " ⚠️ \n\n" + style_text("Check Live Status on Encoder Logs .")
    
    HELP_MESSAGE = style_text(Config.HELP_MESSAGE)
    ABOUT_TEXT = style_text(Config.ABOUT_MESSAGE)
    HELP_BUTTON = style_text("Help 🛠")
    ABOUT_BUTTON = style_text("About ℹ️")
    BACK_BUTTON = style_text("Back 🔙")
    WRONG_MESSAGE = style_text(get_config(
        "STRINGS_WRONG_MESSAGE",
        "current CHAT ID: <code>{CHAT_ID}</code>"
    ))
