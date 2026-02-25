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
    LOG_CHANNEL = get_config("LOG_CHANNEL", "Animes_Wine")
    UPDATES_CHANNEL = get_config("UPDATES_CHANNEL", None)
    DUMP_CHANNEL = get_config("DUMP_CHANNEL", None)
    
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

    # Custom Messages
    START_PIC = get_config("START_PIC", "https://i.ibb.co/nM9Ypvmq/jsorg.jpg")
    START_MESSAGE = get_config("START_MESSAGE", "Hᴇʟʟᴏ, \n<blockquote>Tʜɪꜱ ɪꜱ ᴀ Tᴇʟᴇɢʀᴀᴍ <b>Video Encoder Bot</b>. \n\n<b>Pʟᴇᴀꜱᴇ Sᴇɴᴅ ᴍᴇ ᴀɴʏ Tᴇʟᴇɢʀᴀᴍ Bɪɢ Vɪᴅᴇᴏ Fɪʟᴇ ɪ ᴡɪʟʟ Cᴏᴍᴘʀᴇꜱꜱ Iᴛ ᴀꜱ  Sᴍᴀʟʟ Vɪᴅᴇᴏ Fɪʟᴇ!</b> \n\n/help Fᴏʀ Mᴏʀᴇ Dᴇᴛᴀɪʟꜱ.</blockquote> \n✨ Eɴᴊᴏʏ.....")
    HELP_MESSAGE = get_config("HELP_MESSAGE", "Hi, I am Video Compressor Bot\n\n<b>Available Commands:</b>\n1. Send any video to compress it.\n2. /merge - Start a merge session.\n3. /done - Finish and merge videos in session.\n4. /mediainfo - Reply to a video for MediaInfo (Telegraph).\n5. /hsub - Reply to a subtitle file (replied to a video) for hard subs.\n6. /trim - Usage: `/trim start_time end_time`")
    ABOUT_MESSAGE = get_config("ABOUT_MESSAGE", "<blockquote><b>Mʏ Nᴀᴍᴇ:</b> Zᴀɴɪ Eɴᴄᴏᴅᴇʀ Bᴏᴛ\n<b>Lᴀɴɢᴜᴀɢᴇ:</b> Pʏᴛʜᴏɴ\n<b>Lɪʙʀᴀʀʏ:</b> Pʏʀᴏɢʀᴀᴍ\n<b>Dᴇᴠᴇʟᴏᴘᴇʀ:</b> @TheAlphaBotz</blockquote>")
    
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

