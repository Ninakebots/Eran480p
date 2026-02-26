# Developer: @TheAlphaBotz
# Organization: Anime Junctions
# © 2025 All Rights Reserved

# Developer: @TheAlphaBotz
# Organization: Anime Junctions
# © 2025 All Rights Reserved

from bot.get_cfg import get_config


class Config(object):
    SESSION_NAME = get_config("SESSION_NAME", "Zani")
    APP_ID = int(get_config("APP_ID", "22884130"))
    API_HASH = get_config("API_HASH", "a69e8b16dac958f1bd31eee360ec53fa")
    UPDATES_CHANNEL = get_config("UPDATES_CHANNEL", None)
    DUMP_CHANNEL = get_config("DUMP_CHANNEL", "-1003875340607")
    
    # Auth settings
    AUTH_USERS = [8497538010, -1002809725620]
    AUTH_CHATS = []

    TG_BOT_TOKEN = get_config("TG_BOT_TOKEN", "7437113270:AAEvK-rfb2UTK41zgKUor5S2iF0yixIHemU")
    DOWNLOAD_LOCATION = get_config("DOWNLOAD_LOCATION", "/app/downloads")
    BOT_USERNAME = get_config("BOT_USERNAME", "ZaniEncoderBot")
    
    # File size limits
    MAX_FILE_SIZE = 4194304000
    TG_MAX_FILE_SIZE = 4194304000
    FREE_USER_MAX_FILE_SIZE = 4194304000
    
    # Defaults
    DEF_THUMB_NAIL_VID_S = get_config("DEF_THUMB_NAIL_VID_S", "https://envs.sh/CQU.jpg")
    HTTP_PROXY = get_config("HTTP_PROXY", None)
    MAX_MESSAGE_LENGTH = 4096
    FINISHED_PROGRESS_STR = get_config("FINISHED_PROGRESS_STR", "▣")
    UN_FINISHED_PROGRESS_STR = get_config("UN_FINISHED_PROGRESS_STR", "▢")
    LOG_FILE_ZZGEVC = get_config("LOG_FILE_ZZGEVC", "Log.txt")
    SHOULD_USE_BUTTONS = get_config("SHOULD_USE_BUTTONS", False)
    GOFILE_TOKEN = get_config("GOFILE_TOKEN", None)

    # Custom Messages
    START_PIC = get_config("START_PIC", "https://i.ibb.co/nM9Ypvmq/jsorg.jpg")
    START_MESSAGE = get_config("START_MESSAGE", "👋 **Hᴇʟʟᴏ {mention}!**\n\nI ᴀᴍ ᴀ Pᴏᴡᴇʀғᴜʟ **Vɪᴅᴇᴏ Eɴᴄᴏᴅᴇʀ Bᴏᴛ** ᴡʜɪᴄʜ ᴄᴀɴ Cᴏᴍᴘʀᴇss Vɪᴅᴇᴏs ᴛᴏ Sᴍᴀʟʟ Sɪᴢᴇ ᴡɪᴛʜᴏᴜᴛ ʟᴏsɪɴɢ ǫᴜᴀʟɪᴛʏ.\n\n<blockquote>Sᴇɴᴅ ᴍᴇ ᴀɴʏ Vɪᴅᴇᴏ ᴛᴏ Sᴛᴀʀᴛ Cᴏᴍᴘʀᴇssɪᴏɴ!</blockquote>\n\n**Mᴀɪɴᴛᴀɪɴᴇᴅ Bʏ: [𝖳𝖾𝖺𝗆 𝖶𝗂𝗇𝖾](https://t.me/Team_Wine)**")
    HELP_MESSAGE = get_config("HELP_MESSAGE", "📖 **Hᴇʟᴘ Mᴇɴᴜ**\n\nI ᴄᴀɴ ᴄᴏᴍᴘʀᴇss, ᴍᴇʀɢᴇ, ᴀɴᴅ ᴇᴅɪᴛ ᴠɪᴅᴇᴏs.\n\n**Aᴠᴀɪʟᴀʙʟᴇ Cᴏᴍᴍᴀɴᴅs:**\n➥ /start - Sᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ\n➥ /settings - Cʜᴇᴄᴋ ᴄᴜʀʀᴇɴᴛ Sᴇᴛᴛɪɴɢs\n➥ /us - Oᴘᴇɴ Usᴇʀ Sᴇᴛᴛɪɴɢs ᴍᴇɴᴜ\n➥ /merge - Sᴛᴀʀᴛ ᴀ ᴍᴇʀɢᴇ sᴇssɪᴏɴ\n➥ /done - Fɪɴɪsʜ ᴀɴᴅ ᴍᴇʀɢᴇ ᴠɪᴅᴇᴏs\n➥ /sub - Rᴇᴘʟʏ ᴛᴏ ᴠɪᴅᴇᴏ ᴛᴏ ᴀᴅᴅ sᴜʙᴛɪᴛʟᴇs\n➥ /mediainfo - Gᴇᴛ ᴅᴇᴛᴀɪʟᴇᴅ ᴍᴇᴅɪᴀ ɪɴғᴏ\n➥ /gofile - Uᴘʟᴏᴀᴅ ᴛᴏ GᴏFɪʟᴇ.ɪᴏ\n➥ /speedtest - Cʜᴇᴄᴋ sᴇʀᴠᴇʀ sᴘᴇᴇᴅ\n➥ /sysinfo - Gᴇᴛ sʏsᴛᴇᴍ sᴛᴀᴛs\n➥ /cancel - Cᴀɴᴄᴇʟ ᴀɴ ᴀᴄᴛɪᴠᴇ ᴛᴀsᴋ\n\n**Hᴏᴡ ᴛᴏ ᴜsᴇ:**\n1. Jᴜsᴛ sᴇɴᴅ ᴀɴʏ ᴠɪᴅᴇᴏ ᴛᴏ ᴀᴜᴛᴏ-ᴄᴏᴍᴘʀᴇss.\n2. Usᴇ /us ʀᴇᴘʟɪᴇᴅ ᴛᴏ ᴀ ᴠɪᴅᴇᴏ ᴛᴏ ᴀᴄᴄᴇss ᴛᴏᴏʟs ʟɪᴋᴇ Tʀɪᴍ, Aᴜᴅɪᴏ Eᴅɪᴛɪɴɢ, ᴇᴛᴄ.")
    ABOUT_MESSAGE = get_config("ABOUT_MESSAGE", "<blockquote>✨ **Aʙᴏᴜᴛ Tʜɪs Bᴏᴛ** ✨\n\nI ᴀᴍ ᴀ sᴏᴘʜɪsᴛɪᴄᴀᴛᴇᴅ ᴠɪᴅᴇᴏ ᴘʀᴏᴄᴇssɪɴɢ ʙᴏᴛ ʙᴜɪʟᴛ ᴡɪᴛʜ Pʏᴛʜᴏɴ ᴀɴᴅ FFᴍᴘᴇɢ.\n\n<b>🏷 Nᴀᴍᴇ:</b> Zᴀɴɪ Eɴᴄᴏᴅᴇʀ Bᴏᴛ\n<b>🐍 Lᴀɴɢᴜᴀɢᴇ:</b> Python 3.10+\n<b>📚 Lɪʙʀᴀʀʏ:</b> Pyrogram\n<b>👨‍💻 Dᴇᴠᴇʟᴏᴘᴇʀ:</b> @TheAlphaBotz\n<b>📢 Cʜᴀɴɴᴇʟ:</b> @Team_Wine</blockquote>")
    
    # MongoDB Settings
    MONGODB_URL = get_config(
        "MONGODB_URL",
        "mongodb+srv://yoyat19687:byRateKzeofLw90e@cluster0.ysszzi9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    )
    DATABASE_NAME = get_config("DATABASE_NAME", "encoder_bot")
    
    # Legacy compatibility
    DATABASE_URL = MONGODB_URL


# Expose these for legacy imports
AUTH_CHATS = Config.AUTH_CHATS
AUTH_USERS = Config.AUTH_USERS
MONGODB_URL = Config.MONGODB_URL
DATABASE_URL = Config.DATABASE_URL

