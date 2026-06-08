import asyncio
import sys
from typing import List

import click

from models.job import Job
from services.database import Database
from services.telegram import TelegramService
from scrapers.indeed import IndeedScraper
from scrapers.remoteok import RemoteOKScraper
from scrapers.weworkremotely import WeWorkRemotelyScraper
from scrapers.wellfound import WellfoundScraper
from utils.description import fetch_descriptions_parallel, filter_jobs_by_keywords


SCRAPERS = {
    'indeed': IndeedScraper,
    'remoteok': RemoteOKScraper,
    'weworkremotely': WeWorkRemotelyScraper,
    'wellfound': WellfoundScraper,
}


async def run_scrapers(query: str, sites: List[str] = None, indeed_region: str = "br") -> List[Job]:
    if sites is None:
        sites = list(SCRAPERS.keys())
    
    tasks = []
    for site in sites:
        site_key = site.lower()
        if site_key in SCRAPERS:
            if site_key == "indeed":
                scraper = SCRAPERS[site_key](region=indeed_region)
            else:
                scraper = SCRAPERS[site_key]()
            tasks.append(scraper.search(query))
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    jobs = []
    for result in results:
        if isinstance(result, Exception):
            print(f"Error in scraper: {result}")
            continue
        jobs.extend(result)
    
    return jobs


def display_jobs(jobs: List[Job]):
    if not jobs:
        click.echo("No jobs found.")
        return
    
    for i, job in enumerate(jobs, 1):
        click.echo(f"\n{'='*60}")
        click.echo(f"Job #{i}")
        click.echo(f"{'='*60}")
        click.echo(f"Title: {job.title}")
        click.echo(f"Company: {job.company}")
        click.echo(f"Location: {job.location or 'N/A'}")
        if job.salary:
            click.echo(f"Salary: {job.salary}")
        if job.job_type:
            click.echo(f"Type: {job.job_type}")
        click.echo(f"URL: {job.url}")
        click.echo(f"Source: {job.source}")
        if job.sent_to_telegram:
            click.echo("✓ Already sent to Telegram")


@click.group()
def cli():
    """Job Scraper - Search remote jobs from multiple platforms"""
    pass


@cli.command()
@click.argument('query')
@click.option('--sites', '-s', default=None, help='Comma-separated list of sites (indeed,remoteok,weworkremotely,wellfound)')
@click.option('--remote/--no-remote', default=True, help='Search remote jobs only')
@click.option('--indeed-region', type=click.Choice(['br', 'world']), default='br', show_default=True, help='Indeed region: br or world')
def search(query: str, sites: str, remote: bool, indeed_region: str):
    """Search for jobs across multiple platforms"""
    site_list = sites.split(',') if sites else None
    
    click.echo(f"Searching for: {query}")
    if site_list:
        click.echo(f"Sites: {', '.join(site_list)}")
    else:
        click.echo("Sites: All")
    if not site_list or 'indeed' in [site.lower() for site in site_list]:
        click.echo(f"Indeed region: {indeed_region}")
    
    click.echo("\nStarting scrapers...")
    
    jobs = asyncio.run(run_scrapers(query, site_list, indeed_region))
    
    click.echo(f"Fetching job descriptions...")
    jobs = asyncio.run(fetch_descriptions_parallel(jobs))
    
    click.echo(f"Filtering jobs by keywords...")
    jobs = filter_jobs_by_keywords(jobs)
    
    db = Database()
    saved = db.save_jobs(jobs)
    
    click.echo(f"\nFound {len(jobs)} jobs, saved {saved} new jobs to database.")


@cli.command()
@click.option('--all/--unsent', default=False, help='Show all jobs or only unsent')
def list(all: bool):
    """List jobs from database"""
    db = Database()
    
    if all:
        jobs = db.get_all_jobs()
    else:
        jobs = db.get_unsent_jobs()
    
    click.echo(f"\nFound {len(jobs)} jobs in database.\n")
    display_jobs(jobs)


@cli.command()
def send():
    """Send unsent jobs to Telegram"""
    db = Database()
    jobs = db.get_unsent_jobs()
    
    if not jobs:
        click.echo("No unsent jobs to send.")
        return
    
    click.echo(f"Found {len(jobs)} unsent jobs.")
    
    try:
        telegram = TelegramService()
        sent, failed = telegram.send_jobs(jobs)
        
        if sent > 0:
            urls = [job.url for job in jobs[:sent]]
            db.mark_all_as_sent(urls)
        
        click.echo(f"\nSent: {sent}, Failed: {failed}")
    except ValueError as e:
        click.echo(f"Error: {e}")
        click.echo("Please configure TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env file")


@cli.command()
@click.confirmation_option(prompt='Are you sure you want to delete all jobs?')
def clear():
    """Clear all jobs from database"""
    db = Database()
    db.clear_all()
    click.echo("All jobs cleared from database.")


@cli.command()
def count():
    """Show job count in database"""
    db = Database()
    count = db.get_count()
    click.echo(f"Total jobs in database: {count}")


if __name__ == '__main__':
    cli()
