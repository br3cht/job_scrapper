from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass
class Job:
    title: str
    company: str
    url: str
    source: str
    description: Optional[str] = None
    salary: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[str] = None
    posted_date: Optional[str] = None
    created_at: Optional[datetime] = None
    sent_to_telegram: bool = False
    keywords_found: Optional[List[str]] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

    def to_dict(self):
        return {
            'title': self.title,
            'company': self.company,
            'url': self.url,
            'source': self.source,
            'description': self.description,
            'salary': self.salary,
            'location': self.location,
            'job_type': self.job_type,
            'posted_date': self.posted_date,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'sent_to_telegram': self.sent_to_telegram,
            'keywords_found': self.keywords_found,
        }

    def to_telegram_message(self) -> str:
        msg = f"🏢 *{self.company}*\n"
        msg += f"💼 *{self.title}*\n"
        if self.location:
            msg += f"📍 {self.location}\n"
        if self.salary:
            msg += f"💰 {self.salary}\n"
        if self.job_type:
            msg += f"📋 {self.job_type}\n"
        if self.posted_date:
            msg += f"🕐 {self.posted_date}\n"
        msg += f"🔗 [Ver vaga]({self.url})\n"
        msg += f"📌 Fonte: {self.source}"
        return msg

    def __hash__(self):
        return hash(self.url)

    def __eq__(self, other):
        if isinstance(other, Job):
            return self.url == other.url
        return False
