from abc import ABC, abstractmethod
from typing import List

from models.job import Job

class BaseScraper(ABC):
    def __init__(self):
        self.source_name = self.__class__.__name__.replace('Scraper', '')

    @abstractmethod
    async def search(self, query: str, remote_only: bool = True) -> List[Job]:
        pass

    def _build_url(self, base_url: str, query: str) -> str:
        return base_url.format(query=query.replace(' ', '+'))
