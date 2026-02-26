

import logging
import os
import sys

from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler

from database import init_db
from handlers import (
    start_command,
    help_command,
    list_command,
    delete_command,
    done_callback,
    build_add_conversation_handler,
)
from scheduler import create_scheduler


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)



def main() -> None:
    load_dotenv()
    token = os.getenv("BOT_TOKEN")

    if not token:
        logger.critical(
            "BOT_TOKEN is not set! "
            "Create a .env file with BOT_TOKEN=<your_token> and try again."
        )
        sys.exit(1)

    logger.info("Starting Telegram Reminder Bot...")

    init_db()

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("list", list_command))
    app.add_handler(CommandHandler("delete", delete_command))
    app.add_handler(CallbackQueryHandler(done_callback, pattern=r"^done:\d+$"))

    app.add_handler(build_add_conversation_handler())

  
    scheduler = create_scheduler(bot=app.bot)

    async def on_startup(application) -> None:
        scheduler.start()
        logger.info("Scheduler started. Reminders will be checked every 60 seconds.")

    async def on_shutdown(application) -> None:
        if scheduler.running:
            scheduler.shutdown(wait=False)
            logger.info("Scheduler stopped.")

    app.post_init    = on_startup
    app.post_shutdown = on_shutdown

    logger.info("Bot is running. Press Ctrl+C to stop.")
    app.run_polling(
        poll_interval=1,     
        drop_pending_updates=True, 
    )


if __name__ == "__main__":
    main()
