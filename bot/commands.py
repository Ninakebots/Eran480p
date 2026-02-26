from bot.get_cfg import get_config

class Command:
    START = get_config("COMMAND_START", "start")
    SUB = get_config("COMMAND_SUB", "sub")
    HSUB = get_config("COMMAND_HSUB", "hsub")
    COMPRESS = get_config("COMMAND_COMPRESS", "compress")
    CANCEL = get_config("COMMAND_CANCEL", "cancel")
    STATUS = get_config("COMMAND_STATUS", "status")
    EXEC = get_config("COMMAND_EXEC", "exec")
    HELP = get_config("COMMAND_HELP", "help")
    UPLOAD_LOG_FILE = get_config("COMMAND_UPLOAD_LOG_FILE", "log")
    P480 = "480p"
    P720 = "720p"
    P1080 = "1080p"
    ALL = "all"
    SOFTSUB = "softsub"
    HARDSUB = "hardsub"
    MEDIAINFO = "mediainfo"
    MERGE = "merge"
    DONE = "done"
    LIST = "list"
    SPEEDTEST = "speedtest"
    SYSINFO = "sysinfo"
    GOFILE = "gofile"
