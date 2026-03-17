import asyncio
from typing import List
from playwright.async_api import async_playwright

from scrapers.base import BaseScraper
from models.job import Job


class IndeedScraper(BaseScraper):
    BASE_URL = "https://www.indeed.com/jobs?q={query}&l=Remote"

    async def search(self, query: str, remote_only: bool = True) -> List[Job]:
        jobs = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            url = self.BASE_URL.format(query=query.replace(' ', '+'))
            await page.goto(url)
            
            await page.wait_for_selector('.job-card', timeout=10000)
            
            job_cards = await page.query_selector_all('.job-card')
            
            for card in job_cards[:20]:
                try:
                    title_elem = await card.query_selector('.jobTitle')
                    title = await title_elem.inner_text() if title_elem else "N/A"
                    
                    company_elem = await card.query_selector('.companyName')
                    company = await company_elem.inner_text() if company_elem else "N/A"
                    
                    url_elem = await card.query_selector('a')
                    url = await url_elem.get_attribute('href') if url_elem else ""
                    if url and not url.startswith('http'):
                        url = f"https://www.indeed.com{url}"
                    
                    location_elem = await card.query_selector('.companyLocation')
                    location = await location_elem.inner_text() if location_elem else "Remote"
                    
                    salary_elem = await card.query_selector('.salary-snippet')
                    salary = await salary_elem.inner_text() if salary_elem else None
                    
                    jobs.append(Job(
                        title=title.strip(),
                        company=company.strip(),
                        url=url,
                        source="Indeed",
                        location=location.strip() if location else "Remote",
                        salary=salary.strip() if salary else None
                    ))
                except Exception as e:
                    print(f"Error parsing Indeed job: {e}")
                    continue
            
            await browser.close()
        
        return jobs
