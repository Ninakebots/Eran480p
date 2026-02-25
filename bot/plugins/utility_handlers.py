from pyrogram import filters
from bot import AUTH_USERS, BOT_USERNAME, data, app
from bot.commands import Command
from bot.helper_funcs.utils import sysinfo

@app.on_message(filters.incoming & filters.command([Command.LIST, f"{Command.LIST}@{BOT_USERNAME}"]))
async def list_handler(client, message):
    if message.from_user.id not in AUTH_USERS:
        return
    if not data:
        return await message.reply_text("📚 Queue is empty.")

    text = "📚 **Active Queue:**\n\n"
    for i, task in enumerate(data):
        task_type = task.get('task_type')
        msg = task.get('message')
        text += f"{i+1}. **{task_type}** - ID: `{task.get('id')}`\n"

    await message.reply_text(text)

@app.on_message(filters.incoming & filters.command([Command.SYSINFO, f"{Command.SYSINFO}@{BOT_USERNAME}"]))
async def sysinfo_handler(client, message):
    if message.from_user.id not in AUTH_USERS:
        return
    await sysinfo(message)

@app.on_message(filters.incoming & filters.command([Command.SPEEDTEST, f"{Command.SPEEDTEST}@{BOT_USERNAME}"]))
async def speedtest_handler(client, message):
    if message.from_user.id not in AUTH_USERS:
        return
    sent = await message.reply_text("🏎 Running speed test...")
    import subprocess
    try:
        output = subprocess.check_output(['speedtest-cli', '--simple'], stderr=subprocess.STDOUT).decode()
        await sent.edit_text(f"🏎 **Speed Test Results:**\n\n`{output}`")
    except Exception as e:
        await sent.edit_text(f"❌ speedtest-cli failed or not installed.\nError: {e}")

@app.on_message(filters.incoming & filters.command([Command.CANCEL, f"{Command.CANCEL}@{BOT_USERNAME}"]))
async def cancel_handler(client, message):
    if message.from_user.id not in AUTH_USERS:
        return
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
