from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import models, schemas, auth
from app.database import get_db
from app.services.job_sources import fetch_adzuna_jobs, fetch_jooble_jobs
from app.services.matching import rank_jobs

router = APIRouter(prefix="/jobs", tags=["jobs"])


async def _fetch_from_all_sources(
    db: Session,
    query: str,
    location: str | None,
    salary_min: float | None,
) -> tuple[list[models.Job], list[str]]:
    """Trae vacantes de TODAS las fuentes configuradas (Adzuna + Jooble), las guarda
    evitando duplicados, y regresa (vacantes_guardadas, errores_por_fuente).
    Si una fuente falla (ej. no tiene API key configurada) no tumba a las demas."""
    all_raw = []
    errors = []

    try:
        all_raw += await fetch_adzuna_jobs(query=query, location=location, salary_min=salary_min)
    except RuntimeError as e:
        errors.append(f"Adzuna: {e}")

    try:
        all_raw += await fetch_jooble_jobs(query=query, location=location, salary_min=salary_min)
    except RuntimeError as e:
        errors.append(f"Jooble: {e}")

    if not all_raw and errors:
        # ninguna fuente funciono -> es un error real que reportar
        raise HTTPException(status_code=400, detail=" | ".join(errors))

    saved = []
    for item in all_raw:
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
    return saved, errors


@router.get("", response_model=list[schemas.JobOut])
def list_jobs(db: Session = Depends(get_db), limit: int = 50):
    return db.query(models.Job).order_by(models.Job.fetched_at.desc()).limit(limit).all()


@router.post("/search", response_model=list[schemas.JobWithScoreOut])
async def search_jobs(
    query: str = Query(..., description="Palabra clave, ej: 'data analyst'"),
    location: str | None = Query(None),
    salary_min: float | None = Query(None, description="Sueldo minimo esperado"),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """Busca vacantes reales (Adzuna + Jooble combinados) y regresa cada una ya con
    su score de match contra el CV del usuario, en una sola llamada."""
    cv = db.query(models.CV).filter(models.CV.user_id == current_user.id).first()
    if not cv:
        raise HTTPException(status_code=400, detail="Primero sube tu CV en Mi perfil")

    saved_jobs, _ = await _fetch_from_all_sources(db, query, location, salary_min)

    prefs = db.query(models.Preference).filter(models.Preference.user_id == current_user.id).first()
    ranked = rank_jobs(cv, prefs, saved_jobs, min_score=0.0)

    results = []
    for job, result in ranked:
        results.append(schemas.JobWithScoreOut(
            **schemas.JobOut.model_validate(job).model_dump(),
            score=result.score,
            explanation=result.explanation,
        ))
    return results


@router.post("/fetch", response_model=list[schemas.JobOut])
async def fetch_jobs(
    query: str = Query(..., description="Palabra clave, ej: 'data analyst'"),
    location: str | None = Query(None),
    salary_min: float | None = Query(None, description="Sueldo minimo esperado"),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """Trae vacantes reales (Adzuna + Jooble combinados) y las guarda."""
    saved, _ = await _fetch_from_all_sources(db, query, location, salary_min)
    return saved


@router.post("/fetch-my-preferences", response_model=list[schemas.JobOut])
async def fetch_jobs_from_preferences(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """Igual que /fetch, pero usa automaticamente los 'roles deseados' guardados
    en las preferencias del usuario -- no requiere escribir ninguna palabra clave."""
    prefs = db.query(models.Preference).filter(models.Preference.user_id == current_user.id).first()
    if not prefs or not prefs.desired_roles:
        raise HTTPException(
            status_code=400,
            detail="Primero configura al menos un rol deseado en tus preferencias",
        )

    location = prefs.locations[0] if prefs.locations else None
    saved_all = []
    for role in prefs.desired_roles:
        saved, _ = await _fetch_from_all_sources(db, role, location, prefs.min_salary)
        saved_all += saved
    return saved_all
