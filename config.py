import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

DATABASE_PATH = os.getenv('DATABASE_PATH', 'jobs.db')

SCROLL_PAUSE = 1.5
PAGE_TIMEOUT = 30000

KEYWORDS = ['php', 'remote', 'laravel', 'vue', 'react', 'python', 'javascript', 'node', 'django', 'flask', 'typescript', 'sql', 'mysql', 'postgres', 'mongodb', 'docker', 'kubernetes', 'aws', 'gcp', 'azure', 'linux', 'git', 'api', 'rest', 'graphql', 'agile', 'scrum']

DESCRIPTION_TIMEOUT = 10
