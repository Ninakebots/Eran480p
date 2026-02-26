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

    async def get_user_data(self, user_id: int) -> dict:
        return await self.get_user_settings(user_id)

db = Database()

async def get_user_data(user_id: int) -> dict:
    return await db.get_user_data(user_id)

async def update_user_data(user_id: int, data: dict) -> bool:
    return await db.update_user_data(user_id, data)
