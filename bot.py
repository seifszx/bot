Enterfrom telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# توكن البوت (استبدله بتوكنك الجديد)
TOKEN = "8531850036:AAHnfGVBm7PxNkPVeqUXdrOGD0C-apBGZDo"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الحصول على معرف المستخدم"""
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        f"مرحباً! معرف المستخدم الخاص بك هو:\n`{chat_id}`\n\n"
        f"ضع هذا المعرف في ملف app.py متغير CHAT_ID",
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أرسل /start للحصول على معرف المستخدم")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    print("بوت الإشعارات يعمل...")
    app.run_polling()

if __name__ == "__main__":
    main()
