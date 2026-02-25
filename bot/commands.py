from bot.get_cfg import get_config

class Command:
    START = get_config("COMMAND_START", "start")
    COMPRESS = get_config("COMMAND_COMPRESS", "compress")
    CANCEL = get_config("COMMAND_CANCEL", "cancel")
    STATUS = get_config("COMMAND_STATUS", "status")
    EXEC = get_config("COMMAND_EXEC", "exec")
    HELP = get_config("COMMAND_HELP", "help")
    UPLOAD_LOG_FILE = get_config("COMMAND_UPLOAD_LOG_FILE", "log")
    SET_WATERMARK = get_config("COMMAND_SET_WATERMARK", "set")
    CHECK_WATERMARK = get_config("COMMAND_CHECK_WATERMARK", "watermark")
    P480 = "480p"
    P720 = "720"
    P1080 = "1080p"
    ALL = "all"
    EXTRACT_AUDIO = "extract_audio"
    ADDAUDIO = "addaudio"
    REMAUDIO = "remaudio"
    SUB = "sub"
    HSUB = "hsub"
    RSUB = "rsub"
    TRIM = "trim"
    MEDIAINFO = "mediainfo"
    LIST = "list"
    SPEEDTEST = "speedtest"
    SYSINFO = "sysinfo"
    SAVETHUMBNAIL = "savethumbnail"
    DELETETHUMBNAIL = "deletethumbnail"
