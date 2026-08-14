from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas, auth
from app.database import get_db
from app.services.tailoring import generate_cover_letter, generate_tailored_cv_summary

router = APIRouter(prefix="/applications", tags=["applications"])


@router.post("/from-match/{match_id}", response_model=schemas.ApplicationOut)
def create_application_from_match(
    match_id: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """Genera carta de presentacion + resumen de CV ajustado para una vacante en match.
    No aplica automaticamente: deja todo listo para que el usuario revise y envie
    manualmente en el portal (LinkedIn/Indeed/OCC), respetando sus terminos de servicio."""
    match = db.query(models.Match).filter(
        models.Match.id == match_id, models.Match.user_id == current_user.id
    ).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match no encontrado")

    cv = db.query(models.CV).filter(models.CV.user_id == current_user.id).first()
    if not cv:
        raise HTTPException(status_code=400, detail="Primero sube tu CV")

    job = match.job

    cover_letter = generate_cover_letter(current_user.full_name, cv, job)
    tailored_summary = generate_tailored_cv_summary(cv, job)

    application = models.Application(
        user_id=current_user.id,
        job_id=job.id,
        tailored_cv=tailored_summary,
        cover_letter=cover_letter,
        ready_to_send=True,
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


@router.get("", response_model=list[schemas.ApplicationOut])
def list_applications(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(models.Application)
        .filter(models.Application.user_id == current_user.id)
        .order_by(models.Application.created_at.desc())
        .all()
    )


@router.patch("/{application_id}/submitted", response_model=schemas.ApplicationOut)
def mark_submitted(
    application_id: str,
    payload: schemas.ApplicationMarkSubmitted,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """El usuario confirma que ya aplico manualmente en el portal correspondiente."""
    application = db.query(models.Application).filter(
        models.Application.id == application_id, models.Application.user_id == current_user.id
    ).first()
    if not application:
        raise HTTPException(status_code=404, detail="Aplicacion no encontrada")

    application.submitted_by_user = payload.submitted_by_user
    db.commit()
    db.refresh(application)
    return application
