import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

DATABASE_PATH = os.getenv('DATABASE_PATH', 'jobs.db')

SCROLL_PAUSE = 1.5
PAGE_TIMEOUT = 30000
