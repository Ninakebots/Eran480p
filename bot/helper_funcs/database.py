# Developer: @TheAlphaBotz
# Organization: Anime Junctions
# © 2025 All Rights Reserved

import motor.motor_asyncio
import logging
from typing import Optional
from bot.config import MONGODB_URL

LOGGER = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.client = None
        self.db = None
        self.users = None
        self.auth = None
        
    async def connect(self):
        try:
            if not MONGODB_URL:
                raise Exception("MONGODB_URL not configured in bot/config.py")
                
            self.client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
            self.db = self.client.bot_database
            self.users = self.db.users
            self.auth = self.db.authorized_chats
            
            await self.client.admin.command('ping')
            LOGGER.info("Connected to MongoDB successfully")
        except Exception as e:
            LOGGER.error(f"Error connecting to MongoDB: {e}")
            raise
    

    async def update_user_setting(self, user_id: int, key: str, value) -> bool:
        if self.users is None:
            return False
        try:
            await self.users.update_one(
                {"user_id": user_id},
                {"$set": {key: value}},
                upsert=True
            )
            return True
        except Exception as e:
            LOGGER.error(f"Error updating user setting {key}: {e}")
            return False

    async def get_user_settings(self, user_id: int) -> dict:
        if self.users is None:
            return {}
        try:
            result = await self.users.find_one({"user_id": user_id})
            return result if result else {}
        except Exception as e:
            LOGGER.error(f"Error getting user settings: {e}")
            return {}

    async def update_user_data(self, user_id: int, data: dict) -> bool:
        if self.users is None:
            return False
        try:
            await self.users.update_one(
                {"user_id": user_id},
                {"$set": data},
                upsert=True
            )
            return True
        except Exception as e:
            LOGGER.error(f"Error updating user data: {e}")
            return False

    # Authorization methods
    async def authorize_chat(self, chat_id: int) -> bool:
        if self.auth is None:
            return False
        try:
            await self.auth.update_one(
                {"chat_id": chat_id},
                {"$set": {"is_authorized": True}},
                upsert=True
            )
            return True
        except Exception as e:
            LOGGER.error(f"Error authorizing chat {chat_id}: {e}")
            return False

    async def unauthorize_chat(self, chat_id: int) -> bool:
        if self.auth is None:
            return False
        try:
            await self.auth.delete_one({"chat_id": chat_id})
            return True
        except Exception as e:
            LOGGER.error(f"Error unauthorizing chat {chat_id}: {e}")
            return False

    async def is_chat_authorized(self, chat_id: int) -> bool:
        if self.auth is None:
            return False
        try:
            result = await self.auth.find_one({"chat_id": chat_id})
            return bool(result)
        except Exception as e:
            LOGGER.error(f"Error checking authorization for chat {chat_id}: {e}")
            return False

    async def get_all_authorized_chats(self) -> list:
        if self.auth is None:
            return []
        try:
            cursor = self.auth.find({})
            chats = await cursor.to_list(length=None)
            return [chat['chat_id'] for chat in chats]
        except Exception as e:
            LOGGER.error(f"Error getting all authorized chats: {e}")
            return []

    async def get_global_settings(self, res_key: str) -> dict:
        if self.users is None:
            return {}
        try:
            doc = await self.users.find_one({"user_id": 0})
            if doc and res_key in doc:
                return doc[res_key]

            # Initialization logic if missing
            defaults = {
                "480p": {
                    "codec": "libx264",
                    "audio_codec": "libopus",
                    "crf": "30",
                    "resolution": "854x480",
                    "preset": "superfast",
                    "audio_b": "48k",
                    "video_bitrate": "Auto/None",
                    "bits": "8 bits",
                    "watermark": "None",
                    "wm_size": "0"
                },
                "720p": {
                    "codec": "libx264",
                    "audio_codec": "libopus",
                    "crf": "27",
                    "resolution": "1280x720",
                    "preset": "superfast",
                    "audio_b": "128k",
                    "video_bitrate": "Auto/None",
                    "bits": "8 bits",
                    "watermark": "None",
                    "wm_size": "0"
                },
                "1080p": {
                    "codec": "libx264",
                    "audio_codec": "libopus",
                    "crf": "24",
                    "resolution": "1920x1080",
                    "preset": "superfast",
                    "audio_b": "192k",
                    "video_bitrate": "Auto/None",
                    "bits": "8 bits",
                    "watermark": "None",
                    "wm_size": "0"
                }
            }

            if res_key in defaults:
                await self.update_global_settings(res_key, defaults[res_key])
                return defaults[res_key]

            return {}
        except Exception as e:
            LOGGER.error(f"Error getting global settings: {e}")
            return {}

    async def update_global_settings(self, res_key: str, data: dict) -> bool:
        if self.users is None:
            return False
        try:
            await self.users.update_one(
                {"user_id": 0},
                {"$set": {res_key: data}},
                upsert=True
            )
            return True
        except Exception as e:
            LOGGER.error(f"Error updating global settings: {e}")
            return False

    async def get_user_data(self, user_id: int) -> dict:
        return await self.get_user_settings(user_id)

    async def get_ffmpegcode(self, user_id: int) -> Optional[str]:
        data = await self.get_user_data(user_id)
        return data.get('ffmpeg_code')

    async def get_thumbnail(self, user_id: int) -> Optional[str]:
        import os
        thumb_path = os.path.join("thumbnails", f"{user_id}.jpg")
        return thumb_path if os.path.exists(thumb_path) else None

db = Database()

async def get_user_data(user_id: int) -> dict:
    return await db.get_user_data(user_id)

async def update_user_data(user_id: int, data: dict) -> bool:
    return await db.update_user_data(user_id, data)

async def get_global_settings(res_key: str) -> dict:
    return await db.get_global_settings(res_key)

async def update_global_settings(res_key: str, data: dict) -> bool:
    return await db.update_global_settings(res_key, data)
