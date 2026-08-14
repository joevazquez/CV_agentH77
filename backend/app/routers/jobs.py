from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import models, schemas, auth
from app.database import get_db
from app.services.job_sources import fetch_adzuna_jobs

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=list[schemas.JobOut])
def list_jobs(db: Session = Depends(get_db), limit: int = 50):
    return db.query(models.Job).order_by(models.Job.fetched_at.desc()).limit(limit).all()


@router.post("/fetch", response_model=list[schemas.JobOut])
async def fetch_jobs(
    query: str = Query(..., description="Palabra clave, ej: 'data analyst'"),
    location: str | None = Query(None),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """Trae vacantes reales de Adzuna y las guarda (evita duplicados por external_id)."""
    try:
        raw_jobs = await fetch_adzuna_jobs(query=query, location=location)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))

    saved = []
    for item in raw_jobs:
        existing = db.query(models.Job).filter(
            models.Job.source == item["source"],
            models.Job.external_id == item["external_id"],
        ).first()
        if existing:
            saved.append(existing)
            continue
        job = models.Job(**item)
        db.add(job)
        db.flush()
        saved.append(job)

    db.commit()
    for j in saved:
        db.refresh(j)
    return saved
