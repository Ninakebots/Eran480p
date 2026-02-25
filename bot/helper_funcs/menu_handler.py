from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.helper_funcs.database import get_user_data

class MenuHandler:
    async def main_menu(self, user_id, username):
        text = f"⚙️ **User Settings for** `{username}`\n\nSelect a category to customize your experience:"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎨 Watermark Settings", callback_data="watermark_menu")],
            [InlineKeyboardButton("🛠 Utility Tools", callback_data="utility_menu")],
            [InlineKeyboardButton("❌ Close", callback_data="close_menu")]
        ])
        return text, keyboard

    async def watermark_menu(self, user_id, username):
        user_data = await get_user_data(user_id)
        watermark_url = user_data.get("watermark_url", "None")
        opacity = user_data.get("opacity", 100)
        position = user_data.get("position", "Top Left")
        size = user_data.get("size", 10)

        text = (
            f"🎨 **Watermark Settings for** `{username}`\n\n"
            f"🔗 **URL:** `{watermark_url}`\n"
            f"🌓 **Opacity:** `{opacity}%`\n"
            f"📍 **Position:** `{position}`\n"
            f"📐 **Size:** `{size}%`\n\n"
            "Select an option to modify:"
        )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 Set URL", callback_data="set_watermark_url")],
            [InlineKeyboardButton("🌓 Opacity", callback_data="opacity_menu"),
             InlineKeyboardButton("📐 Size", callback_data="size_menu")],
            [InlineKeyboardButton("📍 Position", callback_data="position_menu")],
            [InlineKeyboardButton("⬅️ Back", callback_data="main_menu"),
             InlineKeyboardButton("❌ Close", callback_data="close_menu")]
        ])
        return text, keyboard

    async def opacity_menu(self, user_id):
        text = "🌓 **Select Watermark Opacity:**"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("25%", callback_data="opacity_25"),
             InlineKeyboardButton("50%", callback_data="opacity_50")],
            [InlineKeyboardButton("75%", callback_data="opacity_75"),
             InlineKeyboardButton("100%", callback_data="opacity_100")],
            [InlineKeyboardButton("⬅️ Back", callback_data="watermark_menu")]
        ])
        return text, keyboard

    async def position_menu(self, user_id):
        text = "📍 **Select Watermark Position:**"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Top Left", callback_data="pos_Top Left"),
             InlineKeyboardButton("Top Right", callback_data="pos_Top Right")],
            [InlineKeyboardButton("Center", callback_data="pos_Center")],
            [InlineKeyboardButton("Bottom Left", callback_data="pos_Bottom Left"),
             InlineKeyboardButton("Bottom Right", callback_data="pos_Bottom Right")],
            [InlineKeyboardButton("⬅️ Back", callback_data="watermark_menu")]
        ])
        return text, keyboard

    async def size_menu(self, user_id):
        text = "📐 **Select Watermark Size (Percentage of video width):**"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("5%", callback_data="size_5"),
             InlineKeyboardButton("10%", callback_data="size_10")],
            [InlineKeyboardButton("15%", callback_data="size_15"),
             InlineKeyboardButton("20%", callback_data="size_20")],
            [InlineKeyboardButton("25%", callback_data="size_25")],
            [InlineKeyboardButton("⬅️ Back", callback_data="watermark_menu")]
        ])
        return text, keyboard

    async def utility_menu(self, user_id):
        text = (
            "🛠 **Utility Tools**\n\n"
            "**Merge:** Send `/merge` to start a session, then send videos.\n"
            "**Audio:** Reply `/addaudio` to an audio file which is a reply to a video.\n"
            "**Subtitles:** Reply `/sub` (soft) or `/hsub` (hard) to a subtitle file.\n\n"
            "More tools coming soon!"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎬 Merge", callback_data="util_merge"),
             InlineKeyboardButton("🎵 Audio", callback_data="util_audio")],
            [InlineKeyboardButton("📝 Subtitles", callback_data="util_sub")],
            [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
        ])
        return text, keyboard

menu_handler = MenuHandler()
