import asyncio
import sys
from pathlib import Path
from typing import List, Optional

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


def _markdown_value(value: Optional[str]) -> str:
    return value.strip() if value else "N/A"


def jobs_to_markdown(jobs: List[Job]) -> str:
    lines = [
        "# Vagas",
        "",
        f"Total: {len(jobs)}",
        "",
    ]

    if not jobs:
        lines.append("Nenhuma vaga encontrada.")
        lines.append("")
        return "\n".join(lines)

    for index, job in enumerate(jobs, 1):
        lines.extend([
            f"## {index}. {_markdown_value(job.title)}",
            "",
            f"- **Empresa:** {_markdown_value(job.company)}",
            f"- **Local:** {_markdown_value(job.location)}",
            f"- **Salario:** {_markdown_value(job.salary)}",
            f"- **Tipo:** {_markdown_value(job.job_type)}",
            f"- **Data:** {_markdown_value(job.posted_date)}",
            f"- **Fonte:** {_markdown_value(job.source)}",
            f"- **URL:** {job.url}",
        ])

        if job.description:
            lines.extend([
                "",
                "### Descricao",
                "",
                job.description.strip(),
            ])

        lines.append("")

    return "\n".join(lines)


def write_jobs_markdown(jobs: List[Job], output_path: str) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(jobs_to_markdown(jobs), encoding="utf-8")
    return path


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
@click.option('--markdown', '-m', 'markdown_path', default=None, type=click.Path(dir_okay=False, writable=True), help='Save listed jobs to a Markdown file')
def list(all: bool, markdown_path: Optional[str]):
    """List jobs from database"""
    db = Database()
    
    if all:
        jobs = db.get_all_jobs()
    else:
        jobs = db.get_unsent_jobs()
    
    click.echo(f"\nFound {len(jobs)} jobs in database.\n")
    display_jobs(jobs)

    if markdown_path:
        path = write_jobs_markdown(jobs, markdown_path)
        click.echo(f"\nMarkdown file generated: {path}")


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


@cli.command()
@click.option('--host', default='0.0.0.0', show_default=True, help='Host to bind')
@click.option('--port', '-p', default=8000, show_default=True, help='Port to bind')
@click.option('--reload', is_flag=True, default=False, help='Enable auto-reload (dev)')
def serve(host: str, port: int, reload: bool):
    """Start the web dashboard"""
    import uvicorn

    click.echo(f"Starting dashboard at http://{host}:{port}")
    uvicorn.run("web.app:app", host=host, port=port, reload=reload)


if __name__ == '__main__':
    cli()
