import asyncio
from typing import List
from playwright.async_api import async_playwright

from scrapers.base import BaseScraper
from models.job import Job


class RemoteOKScraper(BaseScraper):
    BASE_URL = "https://remoteok.com/remote-{query}-jobs"

    async def search(self, query: str, remote_only: bool = True) -> List[Job]:
        jobs = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            url = self.BASE_URL.format(query=query.replace(' ', '-'))
            await page.goto(url)
            
            await page.wait_for_selector('tr.job', timeout=10000)
            
            job_rows = await page.query_selector_all('tr.job')
            
            for row in job_rows[:20]:
                try:
                    title_elem = await row.query_selector('.job-link')
                    title = await title_elem.inner_text() if title_elem else "N/A"
                    
                    company_elem = await row.query_selector('.company_link')
                    company = await company_elem.inner_text() if company_elem else "N/A"
                    
                    url = await row.get_attribute('data-href') if await row.get_attribute('data-href') else ""
                    if url and not url.startswith('http'):
                        url = f"https://remoteok.com{url}"
                    
                    location_elem = await row.query_selector('.location')
                    location = await location_elem.inner_text() if location_elem else "Remote"
                    
                    salary_elem = await row.query_selector('.salary')
                    salary = await salary_elem.inner_text() if salary_elem else None
                    
                    tags = await row.query_selector_all('.tag')
                    job_type = None
                    for tag in tags:
                        tag_text = await tag.inner_text()
                        if tag_text in ['Full Time', 'Part Time', 'Contract', 'Freelance']:
                            job_type = tag_text
                            break
                    
                    jobs.append(Job(
                        title=title.strip(),
                        company=company.strip(),
                        url=url,
                        source="RemoteOK",
                        location=location.strip() if location else "Remote",
                        salary=salary.strip() if salary else None,
                        job_type=job_type
                    ))
                except Exception as e:
                    print(f"Error parsing RemoteOK job: {e}")
                    continue
            
            await browser.close()
        
        return jobs
