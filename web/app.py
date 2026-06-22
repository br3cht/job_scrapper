import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from main import SCRAPERS, run_scrapers
from services.database import Database
from services.telegram import TelegramService
from utils.description import fetch_descriptions_parallel, filter_jobs_by_keywords

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="Job Scraper Dashboard")

# In-memory state for the (single-user, local) scrape job.
scrape_state = {
    "running": False,
    "message": "Idle",
    "query": None,
    "started_at": None,
    "finished_at": None,
    "found": 0,
    "saved": 0,
    "error": None,
}
scrape_lock = asyncio.Lock()


class ScrapeRequest(BaseModel):
    query: str
    sites: Optional[List[str]] = None
    indeed_region: str = "br"


async def _run_scrape(query: str, sites: Optional[List[str]], indeed_region: str):
    try:
        scrape_state.update(
            running=True,
            message="Buscando vagas...",
            query=query,
            started_at=datetime.now().isoformat(),
            finished_at=None,
            found=0,
            saved=0,
            error=None,
        )

        jobs = await run_scrapers(query, sites, indeed_region)

        scrape_state["message"] = "Buscando descrições..."
        jobs = await fetch_descriptions_parallel(jobs)

        scrape_state["message"] = "Filtrando por palavras-chave..."
        jobs = filter_jobs_by_keywords(jobs)

        scrape_state["message"] = "Salvando no banco..."
        db = Database()
        saved = db.save_jobs(jobs)

        scrape_state.update(
            message=f"Concluído: {len(jobs)} encontradas, {saved} novas.",
            found=len(jobs),
            saved=saved,
        )
    except Exception as e:  # noqa: BLE001 - surface any scraper failure to the UI
        scrape_state.update(message="Erro durante a busca.", error=str(e))
    finally:
        scrape_state.update(running=False, finished_at=datetime.now().isoformat())


@app.get("/api/stats")
def get_stats():
    return Database().get_stats()


@app.get("/api/sources")
def get_sources():
    return Database().get_sources()


@app.get("/api/jobs")
def get_jobs(
    source: Optional[str] = None,
    sent: Optional[bool] = None,
    q: Optional[str] = None,
    limit: int = 200,
    offset: int = 0,
):
    return Database().get_jobs_dict(
        source=source, sent=sent, search=q, limit=limit, offset=offset
    )


@app.delete("/api/jobs/{job_id}")
def delete_job(job_id: int):
    if not Database().delete_job(job_id):
        raise HTTPException(status_code=404, detail="Vaga não encontrada")
    return {"deleted": job_id}


@app.post("/api/scrape")
async def start_scrape(req: ScrapeRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="A query é obrigatória")

    async with scrape_lock:
        if scrape_state["running"]:
            raise HTTPException(status_code=409, detail="Uma busca já está em andamento")

        sites = req.sites
        if sites:
            invalid = [s for s in sites if s.lower() not in SCRAPERS]
            if invalid:
                raise HTTPException(
                    status_code=400, detail=f"Sites inválidos: {', '.join(invalid)}"
                )

        asyncio.create_task(_run_scrape(req.query, sites, req.indeed_region))

    return {"status": "started"}


@app.get("/api/scrape/status")
def scrape_status():
    return scrape_state


@app.post("/api/send")
def send_to_telegram():
    db = Database()
    jobs = db.get_unsent_jobs()
    if not jobs:
        return {"sent": 0, "failed": 0, "message": "Nenhuma vaga não enviada."}

    try:
        telegram = TelegramService()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    sent, failed = telegram.send_jobs(jobs)
    if sent > 0:
        db.mark_all_as_sent([job.url for job in jobs[:sent]])

    return {"sent": sent, "failed": failed, "message": f"Enviadas: {sent}, Falhas: {failed}"}


@app.get("/api/config")
def get_config():
    return {"sites": list(SCRAPERS.keys())}


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/", StaticFiles(directory=STATIC_DIR), name="static")
