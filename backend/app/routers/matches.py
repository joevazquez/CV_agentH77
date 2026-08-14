from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas, auth
from app.database import get_db
from app.services.matching import rank_jobs

router = APIRouter(prefix="/matches", tags=["matches"])


@router.post("/refresh", response_model=list[schemas.MatchOut])
def refresh_matches(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    """Recalcula matches del usuario contra todas las vacantes guardadas en la BD."""
    cv = db.query(models.CV).filter(models.CV.user_id == current_user.id).first()
    if not cv:
        raise HTTPException(status_code=400, detail="Primero sube tu CV")

    prefs = db.query(models.Preference).filter(models.Preference.user_id == current_user.id).first()
    all_jobs = db.query(models.Job).all()

    ranked = rank_jobs(cv, prefs, all_jobs)

    # limpia matches previos "matched" para no acumular duplicados en cada refresh
    db.query(models.Match).filter(
        models.Match.user_id == current_user.id,
        models.Match.status == models.JobStatus.matched,
    ).delete()

    created = []
    for job, result in ranked[:30]:
        match = models.Match(
            user_id=current_user.id,
            job_id=job.id,
            score=result.score,
            explanation=result.explanation,
            status=models.JobStatus.matched,
        )
        db.add(match)
        created.append(match)

    db.commit()
    for m in created:
        db.refresh(m)
    return created


@router.get("", response_model=list[schemas.MatchOut])
def list_matches(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(models.Match)
        .filter(models.Match.user_id == current_user.id, models.Match.status == models.JobStatus.matched)
        .order_by(models.Match.score.desc())
        .all()
    )
