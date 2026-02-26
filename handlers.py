

import logging
from datetime import datetime

from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from database import (
    upsert_user,
    add_reminder,
    get_reminders,
    delete_reminder,
)

logger = logging.getLogger(__name__)

WAITING_FOR_TEXT = 1
WAITING_FOR_DATE = 2
WAITING_FOR_TIME = 3

TEMP_REMINDER_KEY = "temp_reminder"



def _register_user(update: Update) -> None:
    user = update.effective_user
    upsert_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
    )



async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _register_user(update)

    first_name = update.effective_user.first_name or "there"

    welcome_text = (
        f"👋 Hello, {first_name}! I'm your *Reminder Bot*.\n\n"
        "I'll send you a reminder at the time you choose.\n\n"
        "📋 *Available commands:*\n"
        "/add — Create a new reminder\n"
        "/list — View all your pending reminders\n"
        "/delete — Delete a reminder\n"
        "/help — Show detailed instructions\n\n"
        "Get started by typing /add! 🚀"
    )

    await update.message.reply_text(welcome_text, parse_mode="Markdown")



async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _register_user(update)

    help_text = (
        "🤖 *Reminder Bot — How to Use*\n\n"

        "*Creating a reminder (/add)*\n"
        "1. Type /add\n"
        "2. Enter your reminder text (e.g., _Doctor appointment_)\n"
        "3. Enter the date in YYYY-MM-DD format (e.g., _2026-03-01_)\n"
        "4. Enter the time in HH:MM format (e.g., _14:30_)\n"
        "✅ Your reminder is saved!\n\n"

        "*Listing reminders (/list)*\n"
        "Type /list to see all your upcoming reminders with their IDs and scheduled times.\n\n"

        "*Deleting a reminder (/delete)*\n"
        "Type /delete followed by the reminder ID (e.g., /delete 3).\n"
        "Find the ID using /list.\n\n"

        "*Notifications*\n"
        "At the scheduled time, I'll send a *non-silent* message automatically. "
        "If you want sound/vibration while Telegram is closed, enable notifications "
        "for Telegram and for this chat in your phone settings.\n\n"

        "*Cancelling /add*\n"
        "Type /cancel at any point during the /add flow to stop.\n\n"

        "⏰ Reminders are checked every minute, so delivery is accurate to ~1 minute."
    )

    await update.message.reply_text(help_text, parse_mode="Markdown")



async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    _register_user(update)

    context.user_data.pop(TEMP_REMINDER_KEY, None)

    await update.message.reply_text(
        "📝 *New Reminder*\n\n"
        "Please enter the reminder text:\n"
        "_(e.g., Doctor appointment)_\n\n"
        "Type /cancel to stop.",
        parse_mode="Markdown",
    )
    return WAITING_FOR_TEXT


async def add_receive_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reminder_text = update.message.text.strip()

    if not reminder_text:
        await update.message.reply_text(
            "⚠️ Reminder text cannot be empty. Please try again."
        )
        return WAITING_FOR_TEXT  

    context.user_data[TEMP_REMINDER_KEY] = {"text": reminder_text}

    await update.message.reply_text(
        f"✅ Text saved: *{reminder_text}*\n\n"
        "📅 Now enter the *date* for the reminder:\n"
        "Format: `YYYY-MM-DD`\n"
        "_(e.g., 2026-03-01)_",
        parse_mode="Markdown",
    )
    return WAITING_FOR_DATE


async def add_receive_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    date_str = update.message.text.strip()

    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        await update.message.reply_text(
            "⚠️ Invalid date format. Please use *YYYY-MM-DD*.\n"
            "_(e.g., 2026-03-01)_",
            parse_mode="Markdown",
        )
        return WAITING_FOR_DATE

    today_str = datetime.now().strftime("%Y-%m-%d")
    if date_str < today_str:
        await update.message.reply_text(
            "⚠️ That date is in the past! Please enter a future date."
        )
        return WAITING_FOR_DATE

    context.user_data[TEMP_REMINDER_KEY]["date"] = date_str

    await update.message.reply_text(
        f"✅ Date saved: *{date_str}*\n\n"
        "🕒 Now enter the *time* for the reminder:\n"
        "Format: `HH:MM` (24-hour)\n"
        "_(e.g., 14:30 for 2:30 PM)_",
        parse_mode="Markdown",
    )
    return WAITING_FOR_TIME


async def add_receive_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    time_str = update.message.text.strip()

    try:
        datetime.strptime(time_str, "%H:%M")
    except ValueError:
        await update.message.reply_text(
            "⚠️ Invalid time format. Please use *HH:MM* (24-hour).\n"
            "_(e.g., 14:30)_",
            parse_mode="Markdown",
        )
        return WAITING_FOR_TIME

    temp = context.user_data.get(TEMP_REMINDER_KEY, {})
    reminder_text = temp.get("text")
    date_str = temp.get("date")

    if not reminder_text or not date_str:
        await update.message.reply_text(
            "❌ Something went wrong. Please start over with /add."
        )
        return ConversationHandler.END

    datetime_str = f"{date_str} {time_str}:00"
    remind_at = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")

    if remind_at <= datetime.now():
        await update.message.reply_text(
            "⚠️ That date and time is already in the past! "
            "Please enter a future time."
        )
        return WAITING_FOR_TIME

    user_id = update.effective_user.id
    reminder_id = add_reminder(
        user_id=user_id,
        text=reminder_text,
        remind_at=remind_at,
    )

    context.user_data.pop(TEMP_REMINDER_KEY, None)

    await update.message.reply_text(
        f"🎉 *Reminder saved!*\n\n"
        f"📌 *Text:* {reminder_text}\n"
        f"📅 *Date:* {date_str}\n"
        f"🕒 *Time:* {time_str}\n"
        f"🆔 *ID:* {reminder_id}\n\n"
        f"I'll remind you at {time_str} on {date_str}. ✅",
        parse_mode="Markdown",
    )
    return ConversationHandler.END


async def add_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop(TEMP_REMINDER_KEY, None)

    await update.message.reply_text(
        "❌ Reminder creation cancelled.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END



async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _register_user(update)
    user_id = update.effective_user.id

    reminders = get_reminders(user_id)

    if not reminders:
        await update.message.reply_text(
            "📭 You have no upcoming reminders.\n\n"
            "Use /add to create one!"
        )
        return

    lines = ["📋 *Your Upcoming Reminders:*\n"]

    for reminder in reminders:
        reminder_id = reminder["id"]
        text        = reminder["text"]
        remind_at   = reminder["remind_at"]

      
        try:
            dt = datetime.strptime(remind_at, "%Y-%m-%d %H:%M:%S")
            formatted_time = dt.strftime("%b %d, %Y at %H:%M")
        except ValueError:
            formatted_time = remind_at

        lines.append(f"🔔 *ID {reminder_id}* — {text}\n   📅 {formatted_time}")

    lines.append("\nUse /delete <ID> to remove a reminder.")

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="Markdown"
    )



async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _register_user(update)
    user_id = update.effective_user.id

    if not context.args:
        await update.message.reply_text(
            "⚠️ Please provide a reminder ID.\n"
            "Usage: `/delete 3`\n\n"
            "Use /list to see your reminder IDs.",
            parse_mode="Markdown",
        )
        return

    try:
        reminder_id = int(context.args[0])
        if reminder_id <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text(
            "⚠️ Invalid ID. Please provide a positive whole number.\n"
            "Example: `/delete 3`",
            parse_mode="Markdown",
        )
        return

    deleted = delete_reminder(reminder_id=reminder_id, user_id=user_id)

    if deleted:
        await update.message.reply_text(
            f"✅ Reminder #{reminder_id} has been deleted."
        )
    else:
        await update.message.reply_text(
            f"❌ Could not find reminder #{reminder_id}.\n\n"
            "It may already have been sent or deleted. Use /list to check."
        )


async def done_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return

    await query.answer("Marked as done ✅")

    data = query.data or ""
    if not data.startswith("done:"):
        return

    message = query.message
    if not message or not message.text:
        return

    done_text = f"{message.text}\n\n✅ Done"
    try:
        await query.edit_message_text(
            text=done_text,
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.warning(f"Could not edit done reminder message: {e}")


def build_add_conversation_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("add", add_start)],

        states={
            WAITING_FOR_TEXT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_receive_text)
            ],
            WAITING_FOR_DATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_receive_date)
            ],
            WAITING_FOR_TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_receive_time)
            ],
        },

        fallbacks=[
            CommandHandler("cancel", add_cancel),
            MessageHandler(filters.COMMAND, add_cancel),
        ],

        conversation_timeout=600,
    )
