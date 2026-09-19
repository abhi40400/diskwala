"""Telegram bot that turns a public Google Drive video link into a Telegram video."""

import asyncio
import logging
import os
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import gdown
from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ChatAction
from telegram.error import TelegramError
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # Standard cloud Bot API upload limit.
DOWNLOAD_SLOTS = asyncio.Semaphore(2)

# Optional: comma-separated Telegram user IDs. Leave it blank to let anyone use the bot.
ALLOWED_USER_IDS = {
    int(value)
    for value in os.getenv("ALLOWED_USER_IDS", "").split(",")
    if value.strip().isdigit()
}

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
LOGGER = logging.getLogger(__name__)


def is_google_drive_link(url: str) -> bool:
    """Accept only normal HTTPS Google Drive sharing links."""
    parsed = urlparse(url)
    return parsed.scheme == "https" and parsed.hostname == "drive.google.com"


def user_is_allowed(update: Update) -> bool:
    """Allow everyone unless ALLOWED_USER_IDS is configured."""
    if not ALLOWED_USER_IDS:
        return True
    return bool(update.effective_user and update.effective_user.id in ALLOWED_USER_IDS)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not user_is_allowed(update):
        await update.effective_message.reply_text("You are not allowed to use this bot.")
        return

    await update.effective_message.reply_text(
        "Send a public Google Drive video link.\n\n"
        "The Drive file must be shared as: Anyone with the link.\n"
        "For in-app playback, MP4 (H.264 video + AAC audio) works best."
    )


async def process_drive_link(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    message = update.effective_message
    link = (message.text or "").strip()

    if not user_is_allowed(update):
        await message.reply_text("You are not allowed to use this bot.")
        return

    if not is_google_drive_link(link):
        await message.reply_text(
            "Send a valid Google Drive sharing link, for example:\n"
            "https://drive.google.com/file/d/FILE_ID/view"
        )
        return

    status = await message.reply_text("Downloading the video from Google Drive…")

    try:
        async with DOWNLOAD_SLOTS:
            with tempfile.TemporaryDirectory(prefix="telegram_drive_") as folder:
                video_path = Path(folder) / "video.mp4"

                # fuzzy=True lets gdown read ordinary /file/d/.../view sharing links.
                downloaded_file = await asyncio.to_thread(
                    gdown.download,
                    url=link,
                    output=str(video_path),
                    fuzzy=True,
                    quiet=True,
                )

                if not downloaded_file or not video_path.is_file():
                    raise RuntimeError("Google Drive did not return a downloadable file.")

                size = video_path.stat().st_size
                if size > MAX_UPLOAD_BYTES:
                    await status.edit_text(
                        "This file is larger than 50 MB. The standard Telegram Bot API "
                        "cannot upload it. Compress the video, or use a local Bot API server."
                    )
                    return

                await status.edit_text("Uploading a streamable video to Telegram…")
                await update.effective_chat.send_action(ChatAction.UPLOAD_VIDEO)

                with video_path.open("rb") as video_file:
                    await message.reply_video(
                        video=video_file,
                        filename="video.mp4",
                        supports_streaming=True,
                        caption="Video from Google Drive",
                        connect_timeout=30,
                        read_timeout=120,
                        write_timeout=120,
                    )

        await status.edit_text("✅ Video sent. It should play directly in Telegram.")

    except TelegramError as error:
        LOGGER.warning("Telegram upload failed: %s", error)
        await status.edit_text("Telegram could not upload this video. Try an MP4 under 50 MB.")
    except Exception as error:
        LOGGER.exception("Drive download failed: %s", error)
        await status.edit_text(
            "I could not download that file. Make sure it is a public Google Drive video "
            "and that the Drive download quota has not been exceeded."
        )


def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN is missing. Copy .env.example to .env and add a newly generated token."
        )

    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, process_drive_link)
    )

    LOGGER.info("Bot started")
    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
