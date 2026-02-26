import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError

from database import get_pending_reminders, mark_reminder_sent

logger = logging.getLogger(__name__)

CHECK_INTERVAL_SECONDS = 60


async def send_due_reminders(bot: Bot) -> None:
    pending = get_pending_reminders()

    if not pending:
        return

    logger.info(f"Scheduler: found {len(pending)} due reminder(s).")

    for reminder in pending:
        reminder_id = reminder["id"]
        user_id     = reminder["user_id"]
        text        = reminder["text"]
        remind_at   = reminder["remind_at"]

        message = (
            f"🚨 *[REMINDER]*\n\n"
            f"{text}\n\n"
            f"_(Scheduled for {remind_at})_"
        )
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("✅ Mark as done", callback_data=f"done:{reminder_id}")]]
        )

        try:
            await bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode="Markdown",
                disable_notification=False,
                reply_markup=keyboard,
            )
            logger.info(f"Sent reminder #{reminder_id} to user {user_id}.")
            mark_reminder_sent(reminder_id)
        except TelegramError as e:
            logger.error(
                f"Failed to send reminder #{reminder_id} to user {user_id}: {e}"
            )


def create_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()

    scheduler.add_job(
        func=send_due_reminders,
        trigger=IntervalTrigger(seconds=CHECK_INTERVAL_SECONDS),
        args=[bot],
        id="reminder_check",
        replace_existing=True,
        name="Check and send due reminders",
    )

    logger.info(
        f"Scheduler created. Will check for reminders every "
        f"{CHECK_INTERVAL_SECONDS} seconds."
    )

    return scheduler
