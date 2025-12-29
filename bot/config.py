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
    API_HASH = get_config("API_HASH", "8583442776:AAEBJMmvHd-yMQPamgd4p94eh1DABM1eC9c")
    LOG_CHANNEL = get_config("LOG_CHANNEL", "Animes_Wine")
    UPDATES_CHANNEL = get_config("UPDATES_CHANNEL", None)
    
    # Auth settings
    AUTH_USERS = [-1003580239953]
    AUTH_CHATS = []

    TG_BOT_TOKEN = get_config("TG_BOT_TOKEN", "8532484467:AAHj6YYhJnSlylWLSv6X3s6Yf0g5m5hf2oA")
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

