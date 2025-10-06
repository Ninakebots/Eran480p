# Developer: @TheAlphaBotz
# Organization: Anime Junctions
# © 2025 All Rights Reserved
import os
import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from bot.helper_funcs.database import db
from bot import AUTH_USERS

LOGGER = logging.getLogger(__name__)

AUTH_CHATS = [-1002997864011, -1002945128480]

@Client.on_message(filters.reply & filters.command("set"))
async def set_watermark_image(client: Client, message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if message.chat.type != "private" and user_id not in AUTH_USERS and chat_id not in AUTH_CHATS:
        return await message.reply("🚫 You are not authorized to use this command")
    
    if not message.reply_to_message:
        return await message.reply("❌ Reply to an image to set it as your watermark")
    
    replied_message = message.reply_to_message
    
    if not replied_message.document and not replied_message.photo:
        return await message.reply("❌ Please reply to an image file (PNG format recommended for transparency)")
    
    try:
        status_msg = await message.reply("⏳ Processing watermark image...")
        
        if replied_message.document:
            if not replied_message.document.file_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                return await status_msg.edit("❌ Please upload PNG, JPG, or JPEG files only")
            
            if replied_message.document.file_size > 5 * 1024 * 1024:
                return await status_msg.edit("❌ Image file too large. Please upload files under 5MB")
            
            file_name = replied_message.document.file_name
        else:
            file_name = f"watermark_{user_id}.jpg"
        
        watermarks_dir = "watermarks"
        os.makedirs(watermarks_dir, exist_ok=True)
        
        file_extension = file_name.split('.')[-1].lower()
        watermark_file_path = os.path.join(watermarks_dir, f"watermark_{user_id}.{file_extension}")
        
        if replied_message.document:
            await client.download_media(replied_message.document, file_name=watermark_file_path)
        else:
            await client.download_media(replied_message.photo, file_name=watermark_file_path)
        
        if os.path.exists(watermark_file_path):
            await db.update_user_setting(user_id, "watermark_image_path", watermark_file_path)
            
            await status_msg.edit(
                f"✅ **Watermark image set successfully!**\n\n"
                f"📁 **File:** `{file_name}`\n"
                f"💾 **Size:** `{replied_message.document.file_size if replied_message.document else 'Photo'}`\n\n"
                f"Your custom watermark will now be applied to all encoded videos.\n"
                f"Use `/us` to adjust position, size, and opacity settings."
            )
        else:
            await status_msg.edit("❌ Failed to download watermark image. Please try again.")
            
    except Exception as e:
        LOGGER.error(f"Error setting watermark: {e}")
        await message.reply("❌ An error occurred while processing your watermark image.")

@Client.on_message(filters.command("remove_watermark"))
async def remove_watermark_image(client: Client, message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if message.chat.type != "private" and user_id not in AUTH_USERS and chat_id not in AUTH_CHATS:
        return await message.reply("🚫 You are not authorized to use this command")
    
    try:
        user_settings = await db.get_user_settings(user_id)
        watermark_path = user_settings.get('watermark_image_path')
        
        if watermark_path and os.path.exists(watermark_path):
            os.remove(watermark_path)
        
        await db.update_user_setting(user_id, "watermark_image_path", None)
        
        await message.reply(
            "✅ **Watermark removed successfully!**\n\n"
            "Your encoded videos will no longer have a custom watermark."
        )
        
    except Exception as e:
        LOGGER.error(f"Error removing watermark: {e}")
        await message.reply("❌ An error occurred while removing your watermark.")
