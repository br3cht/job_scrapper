import asyncio
from typing import List, Optional
import aiohttp
from bs4 import BeautifulSoup

from config import KEYWORDS, DESCRIPTION_TIMEOUT
from models.job import Job


async def fetch_job_description(url: str, session: aiohttp.ClientSession) -> Optional[str]:
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=DESCRIPTION_TIMEOUT)) as response:
            if response.status != 200:
                return None
            
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            
            for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
                tag.decompose()
            
            text = soup.get_text(separator=' ', strip=True)
            
            return text[:50000]
    except Exception as e:
        print(f"Error fetching description from {url}: {e}")
        return None


async def fetch_descriptions_parallel(jobs: List[Job], max_concurrent: int = 20) -> List[Job]:
    if not jobs:
        return jobs
    
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def fetch_with_semaphore(job: Job, session: aiohttp.ClientSession):
        async with semaphore:
            description = await fetch_job_description(job.url, session)
            job.description = description
            return job
    
    async with aiohttp.ClientSession(
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    ) as session:
        tasks = [fetch_with_semaphore(job, session) for job in jobs]
        results = await asyncio.gather(*tasks, return_exceptions=True)
    
    valid_results = []
    for result in results:
        if isinstance(result, Exception):
            print(f"Error in fetch_descriptions_parallel: {result}")
            continue
        valid_results.append(result)
    
    return valid_results


def filter_jobs_by_keywords(jobs: List[Job]) -> List[Job]:
    filtered = []
    
    for job in jobs:
        keywords_found = []
        
        search_text = ""
        if job.title:
            search_text += job.title.lower() + " "
        if job.company:
            search_text += job.company.lower() + " "
        if job.description:
            search_text += job.description.lower()
        
        for keyword in KEYWORDS:
            if keyword.lower() in search_text:
                keywords_found.append(keyword)
        
        if keywords_found:
            job.keywords_found = keywords_found
            filtered.append(job)
    
    return filtered
