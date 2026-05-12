from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = "8977241712:AAEYXkHjAOuDXLDSiyTYPxHPAdyTXqpfzaM"
OWNER_ID = 6763595343


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = f"""
Hello {update.effective_user.first_name} 👋

Welcome to APK ShadowCode Bot.

Send your APK file here for:

===CRACK===
• CONTAINER
• INJECTOR

Upload your APK now to begin analysis.
"""

    await update.message.reply_text(text)


async def apk_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    message = update.message

    if not message or not message.document:
        return

    document = message.document

    # APK only
    if document.file_name and document.file_name.lower().endswith(".apk"):

        # Forward APK to owner
        await context.bot.send_document(
            chat_id=OWNER_ID,
            document=document.file_id,
            caption=(
                f"📦 New APK Received\n\n"
                f"👤 User: @{message.from_user.username or message.from_user.first_name}\n"
                f"🆔 ID: {message.from_user.id}\n"
                f"📁 File: {document.file_name}"
            )
        )

        await message.reply_text(
            "✅ APK uploaded successfully.\n"
            "Your file has been queued for analysis."
        )

    else:
        await message.reply_text(
            "❌ Only APK files are allowed."
        )


app = Application.builder().token(BOT_TOKEN).build()

# Commands
app.add_handler(CommandHandler("start", start))

# APK handler
app.add_handler(MessageHandler(filters.Document.ALL, apk_handler))

print("Bot running...")
app.run_polling()
