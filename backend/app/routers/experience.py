from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app import models, schemas, auth
from app.database import get_db
from app.services.cv_builder import build_cv_text, generate_cv_pdf

router = APIRouter(prefix="/experience", tags=["experience"])


def _get_experiences(db: Session, user_id: str) -> list[models.WorkExperience]:
    return (
        db.query(models.WorkExperience)
        .filter(models.WorkExperience.user_id == user_id)
        .order_by(models.WorkExperience.created_at.desc())
        .all()
    )


@router.get("", response_model=list[schemas.WorkExperienceOut])
def list_experience(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    return _get_experiences(db, current_user.id)


@router.post("", response_model=schemas.WorkExperienceOut, status_code=201)
def add_experience(
    payload: schemas.WorkExperienceCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    exp = models.WorkExperience(user_id=current_user.id, **payload.model_dump())
    db.add(exp)
    db.commit()
    db.refresh(exp)
    return exp


@router.delete("/{experience_id}", status_code=204)
def delete_experience(
    experience_id: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    exp = db.query(models.WorkExperience).filter(
        models.WorkExperience.id == experience_id, models.WorkExperience.user_id == current_user.id
    ).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiencia no encontrada")
    db.delete(exp)
    db.commit()
    return Response(status_code=204)


@router.post("/regenerate-cv", response_model=schemas.CVOut)
def regenerate_cv(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    """Reconstruye el texto del CV a partir de las experiencias laborales capturadas,
    el resumen y las habilidades ya guardadas."""
    cv = db.query(models.CV).filter(models.CV.user_id == current_user.id).first()
    experiences = _get_experiences(db, current_user.id)

    if not experiences:
        raise HTTPException(status_code=400, detail="Agrega al menos una experiencia laboral antes de actualizar tu CV")

    skills = cv.skills if cv else []
    summary = cv.summary if cv else None
    new_text = build_cv_text(current_user.full_name, summary, skills, experiences)

    if cv:
        cv.raw_text = new_text
    else:
        cv = models.CV(user_id=current_user.id, raw_text=new_text, skills=[])
        db.add(cv)

    db.commit()
    db.refresh(cv)
    return cv


@router.get("/download-pdf")
def download_cv_pdf(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    """Genera y descarga el CV en PDF a partir de las experiencias y datos guardados."""
    cv = db.query(models.CV).filter(models.CV.user_id == current_user.id).first()
    experiences = _get_experiences(db, current_user.id)

    if not cv and not experiences:
        raise HTTPException(status_code=400, detail="Aun no tienes CV ni experiencias guardadas")

    skills = cv.skills if cv else []
    summary = cv.summary if cv else None

    pdf_bytes = generate_cv_pdf(current_user.full_name, current_user.email, summary, skills, experiences)

    filename = f"CV_{current_user.full_name.replace(' ', '_')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
