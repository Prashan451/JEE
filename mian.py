import os
import sqlite3
import datetime
import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ContextTypes
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ===== CONFIG =====
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")  # Your bot token from BotFather
OWNER_ID = int(os.getenv("YOUR_TELEGRAM_ID"))  # Your Telegram numeric ID
TARGET_DAYS = 90  # Default: 3 months target

# ===== MOTIVATIONAL QUOTES =====
QUOTES = [
    "💪 Small steps every day lead to big results!",
    "📚 Consistency is more important than intensity!",
    "🚀 Focus today, conquer tomorrow!",
    "🌟 Your only competition is yourself!",
    "🔥 Backlog fear? Crush it one lecture at a time!"
]

# ===== DATABASE =====
DB_FILE = "tracker.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS data (
                    id INTEGER PRIMARY KEY,
                    backlog INTEGER,
                    last_update TEXT
                )""")
    # If empty, set initial backlog to 170
    c.execute("SELECT COUNT(*) FROM data")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO data (backlog, last_update) VALUES (?, ?)", (170, datetime.date.today().isoformat()))
    conn.commit()
    conn.close()

def get_data():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT backlog, last_update FROM data WHERE id=1")
    data = c.fetchone()
    conn.close()
    return list(data)

def update_data(backlog, last_update=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if last_update:
        c.execute("UPDATE data SET backlog=?, last_update=? WHERE id=1", (backlog, last_update))
    else:
        c.execute("UPDATE data SET backlog=? WHERE id=1", (backlog,))
    conn.commit()
    conn.close()

# ===== BOT UI =====
def main_menu():
    keyboard = [
        [InlineKeyboardButton("📚 Backlog Status", callback_data="status")],
        [InlineKeyboardButton("💗 Add Lecture", callback_data="add_lecture")],
        [InlineKeyboardButton("⚙ Settings", callback_data="settings")]
    ]
    return InlineKeyboardMarkup(keyboard)

def add_lecture_menu():
    keyboard = [
        [InlineKeyboardButton("💗 +1 Backlog Lecture", callback_data="backlog_done")],
        [InlineKeyboardButton("💜 +1 New Lecture", callback_data="new_done")],
        [InlineKeyboardButton("⏪ Undo Last Entry", callback_data="undo")],
        [InlineKeyboardButton("⬅ Back to Home", callback_data="home")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ===== AUTO DAILY BACKLOG UPDATE =====
def auto_increase_backlog():
    backlog, last_update = get_data()
    today = datetime.date.today()
    last_date = datetime.date.fromisoformat(last_update)
    if today > last_date:
        # Increase for days passed
        for single_day in (last_date + datetime.timedelta(n) for n in range(1, (today - last_date).days + 1)):
            if single_day.weekday() < 6 and single_day.weekday() != 6:  # Mon-Sat
                backlog += 2
        update_data(backlog, today.isoformat())

# ===== BOT COMMANDS =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return await update.message.reply_text("🚫 You are not authorized to use this bot.")
    auto_increase_backlog()
    await update.message.reply_text("💗 Welcome to your JEE Tracker!", reply_markup=main_menu())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return await update.callback_query.answer("Not authorized!", show_alert=True)

    query = update.callback_query
    await query.answer()
    auto_increase_backlog()

    backlog, _ = get_data()
    today_target = backlog / TARGET_DAYS
    today_target = int(today_target) if today_target > 0 else 0

    if query.data == "home":
        await query.edit_message_text("💗 Home Menu", reply_markup=main_menu())

    elif query.data == "status":
        await query.edit_message_text(
            f"📚 Backlog: {backlog} lectures\n"
            f"🎯 Target: {TARGET_DAYS} days\n"
            f"📅 Today's Target: {today_target} lectures",
            reply_markup=main_menu()
        )

    elif query.data == "add_lecture":
        await query.edit_message_text("➕ Add Lecture", reply_markup=add_lecture_menu())

    elif query.data == "backlog_done":
        backlog -= 1
        update_data(backlog)
        await query.edit_message_text("✅ Logged 1 backlog lecture!", reply_markup=add_lecture_menu())

    elif query.data == "new_done":
        backlog -= 0  # New lecture doesn't reduce backlog
        await query.edit_message_text("✅ Logged 1 new lecture!", reply_markup=add_lecture_menu())

    elif query.data == "undo":
        backlog += 1
        update_data(backlog)
        await query.edit_message_text("↩ Last backlog entry undone!", reply_markup=add_lecture_menu())

    elif query.data == "settings":
        await query.edit_message_text("⚙ Settings (coming soon!)", reply_markup=main_menu())

# ===== DAILY REMINDER =====
async def send_daily_reminder(app):
    backlog, _ = get_data()
    today_target = int(backlog / TARGET_DAYS) if backlog > 0 else 0
    quote = random.choice(QUOTES)
    await app.bot.send_message(
        chat_id=OWNER_ID,
        text=f"🎯 Today's Target: {today_target} lectures\n📚 Backlog left: {backlog}\n\n{quote}"
    )

# ===== MAIN =====
def main():
    init_db()
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_daily_reminder, "cron", hour=8, minute=0, args=[app])
    scheduler.start()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()

if __name__ == "__main__":
    main()
  
