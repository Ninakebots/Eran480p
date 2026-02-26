import os
import logging
import speedtest
import subprocess
from pyrogram import filters
from bot import BOT_USERNAME, data, app
from bot.commands import Command
from bot.helper_funcs.utils import sysinfo, is_auth, hbs
from bot.localisation import Localisation

LOGGER = logging.getLogger(__name__)

@app.on_message(filters.incoming & filters.command([Command.LIST, f"{Command.LIST}@{BOT_USERNAME}"]) & is_auth)
async def list_handler(client, message):
    if not data:
        return await message.reply_text("📚 Queue is empty.")

    text = "📚 **Active Queue:**\n\n"
    for i, task in enumerate(data):
        task_type = task.get('task_type')
        msg = task.get('message')
        text += f"{i+1}. **{task_type}** - ID: `{task.get('id')}`\n"

    await message.reply_text(text)

@app.on_message(filters.incoming & filters.command([Command.SYSINFO, f"{Command.SYSINFO}@{BOT_USERNAME}"]) & is_auth)
async def sysinfo_handler(client, message):
    await sysinfo(message)

@app.on_message(filters.incoming & filters.command([Command.SPEEDTEST, f"{Command.SPEEDTEST}@{BOT_USERNAME}"]) & is_auth)
async def speedtest_handler(client, message):
    sent = await message.reply_text("🏎 Running speed test...")
    try:
        st = speedtest.Speedtest(secure=True)
        st.get_best_server()
        st.download()
        st.upload()
        res = st.results.dict()

        isp = res.get('client', {}).get('isp', 'Unknown')
        server = res.get('server', {}).get('sponsor', 'Unknown')
        country = res.get('server', {}).get('country', 'Unknown')
        ping = res.get('ping', 0)
        download = res.get('download', 0)
        upload = res.get('upload', 0)

        text = (
            f"🏎 **Speed Test Results:**\n\n"
            f"🌐 **ISP:** `{isp}`\n"
            f"📡 **Server:** `{server}, {country}`\n\n"
            f"⬇️ **Download:** `{hbs(download / 8)}/s`\n"
            f"⬆️ **Upload:** `{hbs(upload / 8)}/s`\n"
            f"🏓 **Ping:** `{ping} ms`"
        )
        await sent.edit_text(text)
    except Exception as e:
        LOGGER.error(f"Speedtest error: {e}")
        # Fallback to simple speedtest-cli if available
        try:
            output = subprocess.check_output(['speedtest-cli', '--simple'], stderr=subprocess.STDOUT).decode()
            await sent.edit_text(f"🏎 **Speed Test Results (Fallback):**\n\n`{output}`")
        except Exception as err:
            await sent.edit_text(f"❌ Speed test failed.\nError: {e}\nFallback Error: {err}")

@app.on_message(filters.incoming & filters.command([Command.CANCEL, f"{Command.CANCEL}@{BOT_USERNAME}"]) & is_auth)
async def cancel_handler(client, message):
    args = message.text.split(" ")
    if len(args) > 1:
        try:
            task_id = int(args[1])
            found = False
            for i, task in enumerate(data):
                if task.get('id') == task_id:
                    if i == 0:
                        await message.reply_text("❌ Cannot cancel active task with ID. Use /cancel without arguments for active task.")
                    else:
                        data.pop(i)
                        await message.reply_text(f"✅ Task with ID `{task_id}` removed from queue.")
                    found = True
                    break
            if not found:
                # Try index if not ID
                if 1 <= task_id <= len(data):
                    if task_id == 1:
                        await message.reply_text("❌ Cannot cancel active task with Index. Use /cancel without arguments for active task.")
                    else:
                        data.pop(task_id - 1)
                        await message.reply_text(f"✅ Task at index `{task_id}` removed from queue.")
                else:
                    await message.reply_text(f"❌ No task found with ID or Index `{task_id}`.")
        except ValueError:
            await message.reply_text("❌ Invalid task ID/Index format.")
    else:
        from bot.plugins.incoming_message_fn import incoming_cancel_message_f
        await incoming_cancel_message_f(client, message)

@app.on_message(filters.incoming & filters.command([Command.SAVETHUMBNAIL, f"{Command.SAVETHUMBNAIL}@{BOT_USERNAME}"]) & is_auth)
async def save_thumbnail_handler(client, message):
    reply = message.reply_to_message
    if not reply or not reply.photo:
        return await message.reply_text("❌ Reply to a photo to save it as your custom thumbnail.")

    thumb_dir = "thumbnails"
    if not os.path.isdir(thumb_dir):
        os.makedirs(thumb_dir)

    thumb_path = os.path.join(thumb_dir, f"{message.from_user.id}.jpg")
    await client.download_media(message=reply.photo, file_name=thumb_path)
    await message.reply_text(Localisation.SAVED_CUSTOM_THUMB_NAIL)

@app.on_message(filters.incoming & filters.command([Command.DELETETHUMBNAIL, f"{Command.DELETETHUMBNAIL}@{BOT_USERNAME}"]) & is_auth)
async def delete_thumbnail_handler(client, message):
    thumb_path = os.path.join("thumbnails", f"{message.from_user.id}.jpg")
    if os.path.exists(thumb_path):
        os.remove(thumb_path)
        await message.reply_text(Localisation.DEL_ETED_CUSTOM_THUMB_NAIL)
    else:
        await message.reply_text(Localisation.NO_CUSTOM_THUMB_NAIL_FOUND)
