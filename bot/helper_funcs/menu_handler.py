from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.helper_funcs.database import get_user_data

class MenuHandler:
    async def main_menu(self, user_id, username):
        text = f"⚙️ **User Settings for** `{username}`\n\nSelect a category to customize your experience:"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🛠 Utility Tools", callback_data="utility_menu")],
            [InlineKeyboardButton("❌ Close", callback_data="close_menu")]
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
