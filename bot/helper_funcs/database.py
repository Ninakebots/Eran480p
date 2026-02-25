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
        self.collection = None
        
    async def connect(self):
        try:
            if not MONGODB_URL:
                raise Exception("MONGODB_URL not configured in bot/config.py")
                
            self.client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
            self.db = self.client.bot_database
            self.collection = self.db.watermarks
            
            await self.client.admin.command('ping')
            LOGGER.info("Connected to MongoDB successfully")
        except Exception as e:
            LOGGER.error(f"Error connecting to MongoDB: {e}")
            raise
    
    async def set_watermark_url(self, user_id: int, watermark_url: str) -> bool:
        try:
            from datetime import datetime
            await self.collection.update_one(
                {"user_id": user_id},
                {"$set": {"watermark_url": watermark_url, "updated_at": datetime.utcnow()}},
                upsert=True
            )
            return True
        except Exception as e:
            LOGGER.error(f"Error setting watermark URL: {e}")
            return False
    
    async def get_watermark_url(self, user_id: int) -> Optional[str]:
        try:
            result = await self.collection.find_one({"user_id": user_id})
            return result["watermark_url"] if result else None
        except Exception as e:
            LOGGER.error(f"Error getting watermark URL: {e}")
            return None
    
    async def remove_watermark(self, user_id: int) -> bool:
        try:
            await self.collection.delete_one({"user_id": user_id})
            return True
        except Exception as e:
            LOGGER.error(f"Error removing watermark: {e}")
            return False

    async def update_user_setting(self, user_id: int, key: str, value) -> bool:
        try:
            await self.collection.update_one(
                {"user_id": user_id},
                {"$set": {key: value}},
                upsert=True
            )
            return True
        except Exception as e:
            LOGGER.error(f"Error updating user setting {key}: {e}")
            return False

    async def get_user_settings(self, user_id: int) -> dict:
        try:
            result = await self.collection.find_one({"user_id": user_id})
            return result if result else {}
        except Exception as e:
            LOGGER.error(f"Error getting user settings: {e}")
            return {}

    async def update_user_data(self, user_id: int, data: dict) -> bool:
        try:
            await self.collection.update_one(
                {"user_id": user_id},
                {"$set": data},
                upsert=True
            )
            return True
        except Exception as e:
            LOGGER.error(f"Error updating user data: {e}")
            return False

    async def get_user_data(self, user_id: int) -> dict:
        return await self.get_user_settings(user_id)

db = Database()

async def get_user_data(user_id: int) -> dict:
    return await db.get_user_data(user_id)

async def update_user_data(user_id: int, data: dict) -> bool:
    return await db.update_user_data(user_id, data)
