import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import datetime
import schedule
import time
import threading

# --- BOT TOKEN ---
BOT_TOKEN = "8220626774:AAGmSjIccy91W0uj-AwJB0bI4Z1cD82539c"  # Replace with your token

# --- Logging ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- In-Memory Data (Simulates a Database) ---
user_progress = {}
user_reminders = {}

# --- Commands ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"Hi {user.first_name}! 👋 Welcome to your JEE Prep Bot.\n\n"
        "You can use:\n"
        "/remind – Set chapter revision reminders\n"
        "/mocktest – Get mock test links\n"
        "/pyq – Get previous year questions\n"
        "/progress – View your progress"
    )

async def remind(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        chapter = " ".join(context.args)
        user_id = update.effective_user.id
        user_reminders[user_id] = chapter
        await update.message.reply_text(f"🔔 Reminder set for revision of: {chapter}")
    else:
        await update.message.reply_text("Usage: /remind <chapter name>")

async def mocktest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 Mock Test Links:\n"
        "- Physics: https://bit.ly/mock-phy\n"
        "- Chemistry: https://bit.ly/mock-chem\n"
        "- Maths: https://bit.ly/mock-math"
    )

async def pyq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📘 PYQs by subject:\n"
        "- Physics: https://bit.ly/jee-phy-pyq\n"
        "- Chemistry: https://bit.ly/jee-chem-pyq\n"
        "- Maths: https://bit.ly/jee-math-pyq"
    )

async def progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    progress = user_progress.get(user_id, "No progress tracked yet.")
    await update.message.reply_text(f"📈 Your Progress:\n{progress}")

# --- Background Scheduler for Reminders ---
def check_reminders():
    for user_id, chapter in user_reminders.items():
        now = datetime.datetime.now()
        if now.hour == 20:  # Sends reminder at 8 PM
            context.bot.send_message(chat_id=user_id, text=f"🔔 Reminder: Please revise '{chapter}' today!")

def run_scheduler():
    schedule.every(1).minutes.do(check_reminders)
    while True:
        schedule.run_pending()
        time.sleep(1)

# --- Run Bot ---
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("remind", remind))
    app.add_handler(CommandHandler("mocktest", mocktest))
    app.add_handler(CommandHandler("pyq", pyq))
    app.add_handler(CommandHandler("progress", progress))

    # Run reminder scheduler in a background thread
    threading.Thread(target=run_scheduler, daemon=True).start()

    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
  
