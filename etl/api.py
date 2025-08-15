"""
ETL API Service
===============

Service API pour déclencher et monitorer le pipeline ETL.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging
import asyncio
import os
from datetime import datetime
from pathlib import Path
import sys

# Ajout du path pour les imports
sys.path.append(str(Path(__file__).parent.parent))

from etl.orchestrator import ETLOrchestrator
from etl.scraper_adapter import ScraperETLAdapter

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ScrappingBot ETL API",
    description="API pour déclencher et monitorer le pipeline ETL",
    version="1.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# État global des jobs
active_jobs: Dict[str, Dict[str, Any]] = {}
orchestrator = ETLOrchestrator()
adapter = ScraperETLAdapter()


class ETLJobRequest(BaseModel):
    """Modèle de requête pour un job ETL."""
    input_file: str = "listings.json"
    mark_stale_hours: int = 24
    cleanup_days: int = 30


class ScrapingETLRequest(BaseModel):
    """Modèle de requête pour scraping + ETL."""
    location: str = "Montreal"
    property_type: str = "condo"
    run_etl: bool = True


class BatchScrapingRequest(BaseModel):
    """Modèle de requête pour scraping en lot."""
    locations: List[str]
    property_types: List[str]


@app.get("/")
async def root():
    """Page d'accueil de l'API."""
    return {
        "service": "ScrappingBot ETL API",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "etl_full": "/etl/full",
            "etl_transform": "/etl/transform",
            "etl_load": "/etl/load",
            "scrape_and_etl": "/scrape-etl",
            "batch_scrape": "/scrape-etl/batch",
            "jobs": "/jobs",
            "jobs_status": "/jobs/{job_id}"
        }
    }


@app.get("/health")
async def health_check():
    """Vérification de santé du service."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_jobs": len(active_jobs),
        "data_directory": str(orchestrator.data_dir),
        "data_dir_exists": orchestrator.data_dir.exists()
    }


@app.post("/etl/full")
async def run_full_etl(
    request: ETLJobRequest,
    background_tasks: BackgroundTasks
):
    """Lance un pipeline ETL complet."""
    job_id = f"etl_full_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    active_jobs[job_id] = {
        "type": "etl_full",
        "status": "running",
        "started_at": datetime.now().isoformat(),
        "request": request.dict()
    }
    
    background_tasks.add_task(
        run_etl_background,
        job_id,
        "full",
        request
    )
    
    return {
        "job_id": job_id,
        "status": "started",
        "message": "ETL pipeline started in background"
    }


@app.post("/etl/transform")
async def run_transform_etl(
    request: ETLJobRequest,
    background_tasks: BackgroundTasks
):
    """Lance seulement la partie transformation."""
    job_id = f"etl_transform_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    active_jobs[job_id] = {
        "type": "etl_transform",
        "status": "running",
        "started_at": datetime.now().isoformat(),
        "request": request.dict()
    }
    
    background_tasks.add_task(
        run_etl_background,
        job_id,
        "transform",
        request
    )
    
    return {
        "job_id": job_id,
        "status": "started",
        "message": "ETL transform started in background"
    }


@app.post("/etl/load")
async def run_load_etl(
    request: ETLJobRequest,
    background_tasks: BackgroundTasks
):
    """Lance seulement le chargement en base."""
    job_id = f"etl_load_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    active_jobs[job_id] = {
        "type": "etl_load",
        "status": "running",
        "started_at": datetime.now().isoformat(),
        "request": request.dict()
    }
    
    background_tasks.add_task(
        run_etl_background,
        job_id,
        "load",
        request
    )
    
    return {
        "job_id": job_id,
        "status": "started",
        "message": "ETL load started in background"
    }


@app.post("/scrape-etl")
async def run_scraping_and_etl(
    request: ScrapingETLRequest,
    background_tasks: BackgroundTasks
):
    """Lance le scraping puis l'ETL."""
    job_id = f"scrape_etl_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    active_jobs[job_id] = {
        "type": "scrape_etl",
        "status": "running",
        "started_at": datetime.now().isoformat(),
        "request": request.dict()
    }
    
    background_tasks.add_task(
        run_scraping_etl_background,
        job_id,
        request
    )
    
    return {
        "job_id": job_id,
        "status": "started",
        "message": "Scraping and ETL started in background"
    }


@app.post("/scrape-etl/batch")
async def run_batch_scraping(
    request: BatchScrapingRequest,
    background_tasks: BackgroundTasks
):
    """Lance un scraping en lot pour plusieurs localisations."""
    job_id = f"batch_scrape_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    active_jobs[job_id] = {
        "type": "batch_scrape",
        "status": "running",
        "started_at": datetime.now().isoformat(),
        "request": request.dict()
    }
    
    background_tasks.add_task(
        run_batch_scraping_background,
        job_id,
        request
    )
    
    return {
        "job_id": job_id,
        "status": "started",
        "message": f"Batch scraping started for {len(request.locations)} locations and {len(request.property_types)} property types"
    }


@app.get("/jobs")
async def list_jobs():
    """Liste tous les jobs."""
    return {
        "active_jobs": len(active_jobs),
        "jobs": active_jobs
    }


@app.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Récupère le statut d'un job spécifique."""
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return active_jobs[job_id]


@app.delete("/jobs/{job_id}")
async def cancel_job(job_id: str):
    """Annule un job (supprime de la liste)."""
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = active_jobs.pop(job_id)
    return {
        "message": f"Job {job_id} cancelled/removed",
        "job": job
    }


async def run_etl_background(job_id: str, mode: str, request: ETLJobRequest):
    """Exécute l'ETL en arrière-plan."""
    try:
        result = None
        if mode == "full":
            result = orchestrator.run_full_pipeline(
                request.input_file,
                request.mark_stale_hours,
                request.cleanup_days
            )
        elif mode == "transform":
            result = orchestrator.run_transform_only(request.input_file)
        elif mode == "load":
            result = orchestrator.run_load_only(
                request.input_file,
                request.mark_stale_hours,
                request.cleanup_days
            )
        else:
            # Mode non supporté -> lever une erreur pour être capturée et marquée dans le job
            raise ValueError(f"Unknown ETL mode: {mode}")
        
        active_jobs[job_id].update({
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "result": result
        })
        
    except Exception as e:
        active_jobs[job_id].update({
            "status": "error",
            "completed_at": datetime.now().isoformat(),
            "error": str(e)
        })


async def run_scraping_etl_background(job_id: str, request: ScrapingETLRequest):
    """Exécute le scraping + ETL en arrière-plan."""
    try:
        result = adapter.trigger_scraping_and_etl(
            request.location,
            request.property_type,
            request.run_etl
        )
        
        active_jobs[job_id].update({
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "result": result
        })
        
    except Exception as e:
        active_jobs[job_id].update({
            "status": "error",
            "completed_at": datetime.now().isoformat(),
            "error": str(e)
        })


async def run_batch_scraping_background(job_id: str, request: BatchScrapingRequest):
    """Exécute le scraping en lot en arrière-plan."""
    try:
        result = adapter.schedule_regular_scraping(
            request.locations,
            request.property_types
        )
        
        active_jobs[job_id].update({
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "result": result
        })
        
    except Exception as e:
        active_jobs[job_id].update({
            "status": "error",
            "completed_at": datetime.now().isoformat(),
            "error": str(e)
        })


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("ETL_API_PORT", "8788"))
    host = os.getenv("ETL_API_HOST", "0.0.0.0")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
