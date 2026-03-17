import os
from typing import List, Optional

from telegram import Bot
from telegram.error import TelegramError

from models.job import Job
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


class TelegramService:
    def __init__(self, token: Optional[str] = None, chat_id: Optional[str] = None):
        self.token = token or TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or TELEGRAM_CHAT_ID
        
        if not self.token or not self.chat_id:
            raise ValueError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be configured")
        
        self.bot = Bot(token=self.token)

    def send_job(self, job: Job) -> bool:
        try:
            message = job.to_telegram_message()
            self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            return True
        except TelegramError as e:
            print(f"Error sending job to Telegram: {e}")
            return False

    def send_jobs(self, jobs: List[Job]) -> tuple[int, int]:
        sent = 0
        failed = 0
        for job in jobs:
            if self.send_job(job):
                sent += 1
            else:
                failed += 1
        return sent, failed

    def send_message(self, text: str) -> bool:
        try:
            self.bot.send_message(
                chat_id=self.chat_id,
                text=text,
                parse_mode='Markdown'
            )
            return True
        except TelegramError as e:
            print(f"Error sending message to Telegram: {e}")
            return False
