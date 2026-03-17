import sqlite3
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from models.job import Job
from config import DATABASE_PATH


class Database:
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                source TEXT NOT NULL,
                description TEXT,
                salary TEXT,
                location TEXT,
                job_type TEXT,
                posted_date TEXT,
                created_at TEXT NOT NULL,
                sent_to_telegram INTEGER DEFAULT 0
            )
        ''')
        conn.commit()
        conn.close()

    def _row_to_job(self, row) -> Job:
        return Job(
            title=row[1],
            company=row[2],
            url=row[3],
            source=row[4],
            description=row[5],
            salary=row[6],
            location=row[7],
            job_type=row[8],
            posted_date=row[9],
            created_at=datetime.fromisoformat(row[10]) if row[10] else None,
            sent_to_telegram=bool(row[11])
        )

    def save_job(self, job: Job) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO jobs 
                (title, company, url, source, description, salary, location, job_type, posted_date, created_at, sent_to_telegram)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                job.title,
                job.company,
                job.url,
                job.source,
                job.description,
                job.salary,
                job.location,
                job.job_type,
                job.posted_date,
                job.created_at.isoformat() if job.created_at else datetime.now().isoformat(),
                1 if job.sent_to_telegram else 0
            ))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def save_jobs(self, jobs: List[Job]) -> int:
        count = 0
        for job in jobs:
            if self.save_job(job):
                count += 1
        return count

    def get_all_jobs(self) -> List[Job]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM jobs ORDER BY created_at DESC')
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_job(row) for row in rows]

    def get_unsent_jobs(self) -> List[Job]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM jobs WHERE sent_to_telegram = 0 ORDER BY created_at DESC')
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_job(row) for row in rows]

    def mark_as_sent(self, job_url: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('UPDATE jobs SET sent_to_telegram = 1 WHERE url = ?', (job_url,))
        conn.commit()
        conn.close()

    def mark_all_as_sent(self, job_urls: List[str]):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        for url in job_urls:
            cursor.execute('UPDATE jobs SET sent_to_telegram = 1 WHERE url = ?', (url,))
        conn.commit()
        conn.close()

    def clear_all(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM jobs')
        conn.commit()
        conn.close()

    def job_exists(self, url: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM jobs WHERE url = ?', (url,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists

    def get_count(self) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM jobs')
        count = cursor.fetchone()[0]
        conn.close()
        return count
