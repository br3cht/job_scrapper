from typing import List
from urllib.parse import parse_qs, urljoin, urlparse

from playwright.async_api import TimeoutError as PlaywrightTimeoutError, async_playwright

from scrapers.base import BaseScraper
from models.job import Job


class IndeedScraper(BaseScraper):
    REGION_HOSTS = {
        "br": "https://br.indeed.com",
        "world": "https://www.indeed.com",
    }
    CARD_SELECTOR = '.job_seen_beacon, [data-jk], .jobsearch-ResultsList li'

    def __init__(self, region: str = "br"):
        super().__init__()
        self.region = region if region in self.REGION_HOSTS else "br"
        self.host_url = self.REGION_HOSTS[self.region]
        self.base_url = f"{self.host_url}/jobs?q={{query}}&l=Remote"

    async def _first_text(self, parent, selectors: List[str], default: str = "") -> str:
        for selector in selectors:
            elem = await parent.query_selector(selector)
            if elem:
                text = await elem.inner_text()
                if text and text.strip():
                    return text.strip()
        return default

    def _normalize_url(self, url: str) -> str:
        if not url:
            return ""

        absolute_url = urljoin(self.host_url, url)
        parsed = urlparse(absolute_url)
        job_key = parse_qs(parsed.query).get("jk", [""])[0]
        if job_key:
            return f"{self.host_url}/viewjob?jk={job_key}"

        return absolute_url

    async def search(self, query: str, remote_only: bool = True) -> List[Job]:
        jobs = []
        seen_urls = set()
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                page = await browser.new_page(
                    user_agent=(
                        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
                    )
                )
                
                url = self.base_url.format(query=query.replace(' ', '+'))
                await page.goto(url, wait_until="domcontentloaded")
                
                try:
                    await page.wait_for_selector(self.CARD_SELECTOR, timeout=10000)
                except PlaywrightTimeoutError:
                    print("Indeed scraper: no job cards found before timeout.")
                    return jobs
                
                job_cards = await page.query_selector_all(self.CARD_SELECTOR)
                
                for card in job_cards[:20]:
                    try:
                        title = await self._first_text(
                            card,
                            ['h2.jobTitle', '.jobTitle', 'a.jcs-JobTitle', '[data-testid="job-title"]'],
                            "N/A",
                        )
                        company = await self._first_text(
                            card,
                            ['[data-testid="company-name"]', '.companyName', '[data-company-name="true"]'],
                            "N/A",
                        )
                        
                        url_elem = await card.query_selector('a.jcs-JobTitle, h2.jobTitle a, a[href*="/viewjob"]')
                        url = await url_elem.get_attribute('href') if url_elem else ""
                        url = self._normalize_url(url)
                        
                        location = await self._first_text(
                            card,
                            ['[data-testid="text-location"]', '.companyLocation'],
                            "Remote",
                        )
                        salary = await self._first_text(
                            card,
                            ['[data-testid="attribute_snippet_testid"]', '.salary-snippet'],
                        )
                        
                        if title == "N/A" or not url:
                            continue
                        if url in seen_urls:
                            continue
                        seen_urls.add(url)
                        
                        jobs.append(Job(
                            title=title,
                            company=company,
                            url=url,
                            source="Indeed",
                            location=location,
                            salary=salary or None
                        ))
                    except Exception as e:
                        print(f"Error parsing Indeed job: {e}")
                        continue
            finally:
                await browser.close()
        
        return jobs
