import logging
from logging.handlers import RotatingFileHandler
import os
import time
from pyrogram import Client
from bot.config import Config

AUTH_USERS = set(Config.AUTH_USERS)
AUTH_USERS.add(5179011789)
AUTH_USERS = list(AUTH_USERS)
AUTH_CHATS = list(set(Config.AUTH_CHATS))

SESSION_NAME = Config.SESSION_NAME
TG_BOT_TOKEN = Config.TG_BOT_TOKEN
APP_ID = Config.APP_ID
API_HASH = Config.API_HASH

DUMP_CHANNEL = Config.DUMP_CHANNEL
DOWNLOAD_LOCATION = Config.DOWNLOAD_LOCATION
FREE_USER_MAX_FILE_SIZE = Config.FREE_USER_MAX_FILE_SIZE
MAX_MESSAGE_LENGTH = Config.MAX_MESSAGE_LENGTH
FINISHED_PROGRESS_STR = Config.FINISHED_PROGRESS_STR
UN_FINISHED_PROGRESS_STR = Config.UN_FINISHED_PROGRESS_STR
BOT_START_TIME = time.time()
LOG_FILE_ZZGEVC = "Log.txt"
BOT_USERNAME = Config.BOT_USERNAME 
UPDATES_CHANNEL = Config.UPDATES_CHANNEL
GOFILE_TOKEN = Config.GOFILE_TOKEN
data = []
crf = []
resolution = []
audio_b = []
audio_codec_list = []
preset = []
codec = []
pid_list = []
merge_sessions = {}
subtitle_sessions = {}
app = Client(
        SESSION_NAME,
        bot_token=TG_BOT_TOKEN,
        api_id=APP_ID,
        api_hash=API_HASH,
        workers=2
    )
if os.path.exists(LOG_FILE_ZZGEVC):
    with open(LOG_FILE_ZZGEVC, "r+") as f_d:
        f_d.truncate(0)

# the logging things
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[
        RotatingFileHandler(
            LOG_FILE_ZZGEVC,
            maxBytes=FREE_USER_MAX_FILE_SIZE,
            backupCount=10
        ),
        logging.StreamHandler()
    ]
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
LOGGER = logging.getLogger(__name__)
