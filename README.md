# Telegram Google Drive Video Bot

Send this bot a **public Google Drive video link** and it uploads the file as a Telegram video with streaming enabled.

## Important security step

The old bot token was exposed. Before using this project, open [@BotFather](https://t.me/BotFather), revoke or regenerate that token, and use the new token only in your local `.env` file.

Never put a real token in `bot.py`, `README.md`, a Git commit, or a GitHub issue.

## Requirements

- Python 3.10 or newer
- A Telegram bot created through [@BotFather](https://t.me/BotFather)
- A Google Drive file shared as **Anyone with the link**

## Windows setup

```powershell
cd path\to\telegram-drive-video-bot
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Open `.env` and replace the placeholder after `BOT_TOKEN=` with the **new** token from BotFather. Do not add spaces or quotation marks.

Start the bot:

```powershell
python bot.py
```

Open the bot in Telegram, send `/start`, then send a Drive sharing link such as:

```text
https://drive.google.com/file/d/FILE_ID/view?usp=sharing
```

## GitHub upload

`.env` is already excluded by `.gitignore`. Check that it is not being added before publishing:

```powershell
git init
git add bot.py requirements.txt README.md .gitignore .env.example
git status
git commit -m "Add Telegram Drive video bot"
```

Then create an empty GitHub repository and follow its push instructions. Do **not** use `git add .` until you confirm `.env` is ignored.

## Limits and notes

- Standard Telegram Bot API video uploads are limited to 50 MB.
- The bot does not stream directly from Drive; it downloads the public file temporarily, uploads it to Telegram, then deletes the temporary copy.
- MP4 using H.264 video and AAC audio gives the most reliable in-app playback.
- Leaving `ALLOWED_USER_IDS` blank makes the bot public. Set it to your own numeric Telegram ID before deploying publicly, or anyone who finds the bot can request downloads.
