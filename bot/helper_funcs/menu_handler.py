from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.helper_funcs.database import get_user_data, get_global_settings

class MenuHandler:
    async def global_settings_menu(self, res_key="480p", is_admin=False):
        settings = await get_global_settings(res_key)

        codec = settings.get('codec', 'libx264')
        audio_codec = settings.get('audio_codec', 'libopus')
        crf = settings.get('crf', '30')
        res = settings.get('resolution', '854x480')
        preset = settings.get('preset', 'superfast')
        audio_b = settings.get('audio_b', '48k')
        video_b = settings.get('video_bitrate', 'Auto/None')
        bits = settings.get('bits', '8 bits')
        watermark = settings.get('watermark', 'None')
        wm_size = settings.get('wm_size', '0')

        default_str = " (Default)" if res_key == "480p" else ""

        text = (
            f"Tʜᴇ Cᴜʀʀᴇɴᴛ Sᴇᴛᴛɪɴɢꜱ ᴡɪʟʟ ʙᴇ Aᴅᴅᴇᴅ Yᴏᴜʀ Vɪᴅᴇᴏ Fɪʟᴇ ({res_key}{default_str}):\n"
            f"Video Codec : {codec} \n"
            f"Audio Codec : {audio_codec} \n"
            f"Crf : {crf} \n"
            f"Resolution : {res} \n"
            f"Preset : {preset} \n"
            f"Audio Bitrate : {audio_b} \n"
            f"Video Bitrate : {video_b} \n"
            f"Bits : {bits} \n"
            f"Watermark : {watermark}\n"
            f"WM Size : {wm_size} \n"
            "The Ability to Change Settings is Only for Admin"
        )

        buttons = [
            [
                InlineKeyboardButton("480p", callback_data="view_global_480p"),
                InlineKeyboardButton("720p", callback_data="view_global_720p"),
                InlineKeyboardButton("1080p", callback_data="view_global_1080p")
            ]
        ]

        if is_admin:
            buttons.append([InlineKeyboardButton("📝 Change Settings", callback_data=f"settings_menu|global|{res_key}")])

        buttons.append([InlineKeyboardButton("❌ Close", callback_data="close_menu")])

        return text, InlineKeyboardMarkup(buttons)

    async def settings_menu(self, user_id, context=""):
        if "|global|" in context:
            res_key = context.split('|')[-1]
            user_settings = await get_global_settings(res_key)
            title = f"⚙️ **Global Settings ({res_key})**"
        else:
            user_settings = await get_user_data(user_id)
            title = "⚙️ **Personal Settings**"

        codec = user_settings.get('codec', 'libsvtav1')
        crf = user_settings.get('crf', '24')
        preset = user_settings.get('preset', 'veryfast')
        audio = user_settings.get('audio_b', '128k')
        res = user_settings.get('resolution', '480p')

        text = (
            f"{title}\n\n"
            f"🎥 **Codec:** `{codec}`\n"
            f"📊 **CRF:** `{crf}`\n"
            f"⚡ **Preset:** `{preset}`\n"
            f"🎵 **Audio Bitrate:** `{audio}`\n"
            f"🎬 **Resolution:** `{res}`\n\n"
            "Select a setting to change it:"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎥 Codec", callback_data=f"set_codec{context}"),
             InlineKeyboardButton("📊 CRF", callback_data=f"set_crf{context}")],
            [InlineKeyboardButton("⚡ Preset", callback_data=f"set_pre{context}"),
             InlineKeyboardButton("🎵 Audio", callback_data=f"set_aud{context}")],
            [InlineKeyboardButton("🎬 Resolution", callback_data=f"set_res{context}"),
             InlineKeyboardButton("❌ Close", callback_data="close_menu")]
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

        buttons.append([InlineKeyboardButton("⬅️ Back", callback_data=f"settings_menu{context}")])
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
