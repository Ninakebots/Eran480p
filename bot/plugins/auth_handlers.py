from pyrogram import Client, filters
from bot import app, AUTH_USERS, BOT_USERNAME
from bot.commands import Command
from bot.helper_funcs.database import db

@app.on_message(filters.command(["authorize", f"authorize@{BOT_USERNAME}"]) & filters.user(AUTH_USERS))
async def authorize_handler(client, message):
    if len(message.command) > 1:
        try:
            chat_id = int(message.command[1])
        except ValueError:
            return await message.reply_text("❌ Invalid chat ID. Please provide a numeric ID.")
    elif message.reply_to_message and message.reply_to_message.from_user:
        chat_id = message.reply_to_message.from_user.id
    else:
        return await message.reply_text("Provide a chat ID or reply to a message to authorize.")

    if await db.authorize_chat(chat_id):
        await message.reply_text(f"✅ Chat/User {chat_id} authorized.")
    else:
        await message.reply_text("❌ Failed to authorize.")

@app.on_message(filters.command(["unauthorize", f"unauthorize@{BOT_USERNAME}"]) & filters.user(AUTH_USERS))
async def unauthorize_handler(client, message):
    if len(message.command) > 1:
        try:
            chat_id = int(message.command[1])
        except ValueError:
            return await message.reply_text("❌ Invalid chat ID. Please provide a numeric ID.")
    elif message.reply_to_message and message.reply_to_message.from_user:
        chat_id = message.reply_to_message.from_user.id
    else:
        return await message.reply_text("Provide a chat ID or reply to a message to unauthorize.")

    if await db.unauthorize_chat(chat_id):
        await message.reply_text(f"✅ Chat/User {chat_id} unauthorized.")
    else:
        await message.reply_text("❌ Failed to unauthorize.")

@app.on_message(filters.command([Command.AUTHLIST, f"authlist@{BOT_USERNAME}"]) & filters.user(AUTH_USERS))
async def authlist_handler(client, message):
    from bot import AUTH_CHATS

    # Get IDs from database
    db_authorized = await db.get_all_authorized_chats()

    # Combine with hardcoded lists
    all_auth = set(AUTH_USERS + AUTH_CHATS + db_authorized)

    if not all_auth:
        return await message.reply_text("📋 **No authorized IDs found.**")

    text = "📋 **Authorized IDs:**\n\n"
    for i, auth_id in enumerate(all_auth):
        status = ""
        if auth_id in AUTH_USERS:
            status = " (Admin)"
        elif auth_id in AUTH_CHATS:
            status = " (Hardcoded Chat)"
        else:
            status = " (Database)"

        text += f"{i+1}. `{auth_id}`{status}\n"

    await message.reply_text(text)
