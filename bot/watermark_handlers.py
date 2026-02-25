import re
import requests
from pyrogram import Client, filters
from pyrogram.types import Message
from bot.helper_funcs.database import db
from bot.helper_funcs.utils import is_auth
from bot.commands import Command
import logging

LOGGER = logging.getLogger(__name__)

def is_valid_url(url: str) -> bool:
    url_pattern = re.compile(
        r'^https?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return url_pattern.match(url) is not None

def is_image_url(url: str) -> bool:
    try:
        response = requests.head(url, timeout=10)
        content_type = response.headers.get('content-type', '').lower()
        return content_type.startswith('image/')
    except:
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff']
        return any(url.lower().endswith(ext) for ext in image_extensions)

@Client.on_message(filters.command(Command.SET_WATERMARK) & is_auth)
async def set_watermark(client: Client, message: Message):
    user_id = message.from_user.id
    
    try:
        if len(message.command) < 2:
            await message.reply(
                "📝 **How to set watermark:**\n\n"
                f"Use: `/{Command.SET_WATERMARK} <image_url>`\n\n"
                f"**Example:** `/{Command.SET_WATERMARK} https://example.com/watermark.png`\n\n"
                "**Requirements:**\n"
                "• Must be a direct image URL\n"
                "• Supported formats: JPG, PNG, GIF, BMP, WebP\n"
                "• Image should be reasonably sized for watermark\n\n"
                f"**Remove watermark:** `/{Command.SET_WATERMARK} remove`"
            )
            return
        
        watermark_input = message.command[1]
        
        if watermark_input.lower() in ['remove', 'delete', 'clear']:
            success = await db.remove_watermark(user_id)
            if success:
                await message.reply("✅ Watermark removed successfully!")
            else:
                await message.reply("❌ Failed to remove watermark. Please try again.")
            return
        
        if not is_valid_url(watermark_input):
            await message.reply(
                "❌ **Invalid URL format!**\n\n"
                "Please provide a valid URL starting with `http://` or `https://`\n\n"
                f"**Example:** `/{Command.SET_WATERMARK} https://example.com/watermark.png`"
            )
            return
        
        if not is_image_url(watermark_input):
            await message.reply(
                "❌ **Invalid image URL!**\n\n"
                "The URL must point to an image file.\n"
                "Supported formats: JPG, PNG, GIF, BMP, WebP, TIFF\n\n"
                "**Make sure the URL ends with an image extension or returns image content.**"
            )
            return
        
        success = await db.set_watermark_url(user_id, watermark_input)
        
        if success:
            await message.reply(
                f"✅ **Watermark set successfully!**\n\n"
                f"🔗 **URL:** `{watermark_input}`\n\n"
                f"Your videos will now be processed with this watermark.\n\n"
                f"**Commands:**\n"
                f"• `/{Command.SET_WATERMARK} remove` - Remove watermark\n"
                f"• `/{Command.SET_WATERMARK} <new_url>` - Change watermark"
            )
        else:
            await message.reply("❌ Failed to set watermark. Please try again.")
            
    except Exception as e:
        LOGGER.error(f"Error in set_watermark command: {e}")
        await message.reply("❌ An error occurred while setting watermark. Please try again.")

@Client.on_message(filters.command(Command.CHECK_WATERMARK) & is_auth)
async def check_watermark(client: Client, message: Message):
    user_id = message.from_user.id
    
    try:
        watermark_url = await db.get_watermark_url(user_id)
        
        if watermark_url:
            await message.reply(
                f"🎨 **Current Watermark:**\n\n"
                f"🔗 **URL:** `{watermark_url}`\n\n"
                f"**Commands:**\n"
                f"• `/{Command.SET_WATERMARK} <new_url>` - Change watermark\n"
                f"• `/{Command.SET_WATERMARK} remove` - Remove watermark"
            )
        else:
            await message.reply(
                "🎨 **No watermark set!**\n\n"
                f"Use `/{Command.SET_WATERMARK} <image_url>` to set a watermark.\n\n"
                f"**Example:** `/{Command.SET_WATERMARK} https://example.com/watermark.png`"
            )
            
    except Exception as e:
        LOGGER.error(f"Error in check_watermark command: {e}")
        await message.reply("❌ An error occurred while checking watermark.")
