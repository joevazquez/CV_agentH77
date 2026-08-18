"""
Endpoint para automatizar la busqueda de vacantes y el recalculo de matches
para TODOS los usuarios de la plataforma, protegido con un secreto simple
(no requiere login de usuario, pensado para ser llamado por un cron externo).

Como el plan gratuito de Render no ofrece un scheduler propio "siempre
encendido" sin costo, la forma recomendada de programarlo es con un cron
externo gratuito (ej. https://cron-job.org) que le pegue a este endpoint
una vez al dia. Esto tambien tiene el efecto util de "despertar" el backend
antes de que un usuario real lo necesite.
"""
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.orm import Session

from app import models
from app.database import SessionLocal
from app.config import settings
from app.services.job_sources import fetch_adzuna_jobs, fetch_jooble_jobs
from app.services.matching import rank_jobs

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/auto-refresh")
async def auto_refresh_all(secret: str = Query(...)):
    """Dispara: 1) busqueda de vacantes nuevas en Adzuna para cada rol deseado
    unico entre todos los usuarios, y 2) recalculo de matches por usuario.
    Protegido con CRON_SECRET -- llamar como POST /admin/auto-refresh?secret=XXX
    """
    if not settings.cron_secret or secret != settings.cron_secret:
        raise HTTPException(status_code=403, detail="Secreto invalido")

    db: Session = SessionLocal()
    try:
        # 1. Recolectar roles deseados unicos de todos los usuarios con preferencias
        all_prefs = db.query(models.Preference).all()
        unique_roles = set()
        for p in all_prefs:
            for role in (p.desired_roles or []):
                unique_roles.add(role.strip())

        jobs_fetched = 0
        roles_con_error = []
        for role in unique_roles:
            role_had_results = False
            for fetch_fn in (fetch_adzuna_jobs, fetch_jooble_jobs):
                try:
                    raw_jobs = await fetch_fn(query=role)
                except RuntimeError as e:
                    roles_con_error.append({"rol": role, "error": str(e)})
                    continue
                role_had_results = True
                for item in raw_jobs:
                    existing = db.query(models.Job).filter(
                        models.Job.source == item["source"],
                        models.Job.external_id == item["external_id"],
                    ).first()
                    if not existing:
                        db.add(models.Job(**item))
                        jobs_fetched += 1
        db.commit()

        # 2. Recalcular matches para cada usuario que tenga CV
        all_jobs = db.query(models.Job).all()
        users_updated = 0
        for cv in db.query(models.CV).all():
            prefs = db.query(models.Preference).filter(
                models.Preference.user_id == cv.user_id
            ).first()
            ranked = rank_jobs(cv, prefs, all_jobs)

            db.query(models.Match).filter(
                models.Match.user_id == cv.user_id,
                models.Match.status == models.JobStatus.matched,
            ).delete()

            for job, result in ranked[:30]:
                db.add(models.Match(
                    user_id=cv.user_id,
                    job_id=job.id,
                    score=result.score,
                    explanation=result.explanation,
                    status=models.JobStatus.matched,
                ))
            users_updated += 1
        db.commit()

        return {
            "roles_buscados": list(unique_roles),
            "vacantes_nuevas": jobs_fetched,
            "usuarios_actualizados": users_updated,
            "roles_con_error": roles_con_error,
        }
    finally:
        db.close()
