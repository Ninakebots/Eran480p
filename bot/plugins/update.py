from pyrogram import filters
from bot import app, AUTH_USERS, BOT_USERNAME
from bot.commands import Command
from bot.helper_funcs.update import check_for_updates, perform_update, restart_bot
import logging

LOGGER = logging.getLogger(__name__)

@app.on_message(filters.incoming & filters.command([Command.UPDATE, f"{Command.UPDATE}@{BOT_USERNAME}"]))
async def update_handler(client, message):
    if message.from_user.id not in AUTH_USERS:
        return await message.reply_text("🔒 Admin Only")

    args = message.text.split()
    sent = await message.reply_text("🔄 **Checking for updates...**")

    try:
        remote = args[1] if len(args) > 1 else None
        branch = args[2] if len(args) > 2 else None

        has_update, curr, new = await check_for_updates(remote, branch)

        if not has_update:
            return await sent.edit_text("✅ **Bot is already up to date.**")

        await sent.edit_text("🔄 **Updates found! Pulling changes...**")
        out = await perform_update()

        await sent.edit_text(f"✅ **Updated successfully!**\n\n`{out}`\n\nRestarting...")
        restart_bot()

    except Exception as e:
        LOGGER.error(f"Update failed: {e}")
        await sent.edit_text(f"❌ **Update failed.**\n\nError: `{e}`")
