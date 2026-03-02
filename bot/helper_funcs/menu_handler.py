from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.helper_funcs.database import get_user_data

class MenuHandler:
    async def settings_menu(self, user_id, context=""):
        user_settings = await get_user_data(user_id)

        codec = user_settings.get('codec', 'libsvtav1')
        crf = user_settings.get('crf', '24')
        preset = user_settings.get('preset', 'veryfast')
        audio = user_settings.get('audio_b', '128k')

        text = (
            "⚙️ **Personal Settings**\n\n"
            f"🎥 **Codec:** `{codec}`\n"
            f"📊 **CRF:** `{crf}`\n"
            f"⚡ **Preset:** `{preset}`\n"
            f"🎵 **Audio Bitrate:** `{audio}`\n\n"
            "Select a setting to change it:"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎥 Codec", callback_data=f"set_codec{context}"),
             InlineKeyboardButton("📊 CRF", callback_data=f"set_crf{context}")],
            [InlineKeyboardButton("⚡ Preset", callback_data=f"set_pre{context}"),
             InlineKeyboardButton("🎵 Audio", callback_data=f"set_aud{context}")],
            [InlineKeyboardButton("❌ Close", callback_data="close_menu")]
        ])
        return text, keyboard

    async def encoding_settings_menu(self, user_id, context=""):
        # Deprecated for general users, but kept for compatibility during transition if needed
        return await self.settings_menu(user_id, context)

    async def set_codec_menu(self, user_id, context=""):
        text = "🎥 **Select Video Codec:**"
        options = ["libx264", "libx265", "libsvtav1", "libvpx-vp9"]
        buttons = []
        for opt in options:
            buttons.append([InlineKeyboardButton(opt, callback_data=f"upd_codec_{opt}{context}")])
        buttons.append([InlineKeyboardButton("⬅️ Back", callback_data=f"settings_menu{context}")])
        return text, InlineKeyboardMarkup(buttons)

    async def set_res_menu(self, user_id, context=""):
        text = "🎬 **Select Resolution:**"
        options = ["480p", "720p", "1080p", "All"]
        buttons = []
        for i in range(0, len(options), 2):
            row = [InlineKeyboardButton(options[i], callback_data=f"upd_res_{options[i]}{context}")]
            if i + 1 < len(options):
                row.append(InlineKeyboardButton(options[i+1], callback_data=f"upd_res_{options[i+1]}{context}"))
            buttons.append(row)

        if not context:
            buttons.append([InlineKeyboardButton("⬅️ Back", callback_data="back_to_media")])
        else:
            buttons.append([InlineKeyboardButton("❌ Close", callback_data="close_menu")])
        return text, InlineKeyboardMarkup(buttons)

    async def set_crf_menu(self, user_id, context=""):
        text = "📊 **Select CRF (Lower is better quality):**"
        options = ["18", "20", "22", "24", "26", "28", "30"]
        buttons = []
        for i in range(0, len(options), 3):
            row = [InlineKeyboardButton(o, callback_data=f"upd_crf_{o}{context}") for o in options[i:i+3]]
            buttons.append(row)
        buttons.append([InlineKeyboardButton("⬅️ Back", callback_data=f"settings_menu{context}")])
        return text, InlineKeyboardMarkup(buttons)

    async def set_pre_menu(self, user_id, context=""):
        text = "⚡ **Select Preset:**"
        options = ["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow"]
        buttons = []
        for i in range(0, len(options), 2):
            row = [InlineKeyboardButton(o, callback_data=f"upd_pre_{o}{context}") for o in options[i:i+2]]
            buttons.append(row)
        buttons.append([InlineKeyboardButton("⬅️ Back", callback_data=f"settings_menu{context}")])
        return text, InlineKeyboardMarkup(buttons)

    async def set_aud_menu(self, user_id, context=""):
        text = "🎵 **Select Audio Bitrate:**"
        options = ["32k", "48k", "64k", "96k", "128k", "192k"]
        buttons = []
        for i in range(0, len(options), 2):
            row = [InlineKeyboardButton(o, callback_data=f"upd_aud_{o}{context}") for o in options[i:i+2]]
            buttons.append(row)
        buttons.append([InlineKeyboardButton("⬅️ Back", callback_data=f"settings_menu{context}")])
        return text, InlineKeyboardMarkup(buttons)

menu_handler = MenuHandler()
