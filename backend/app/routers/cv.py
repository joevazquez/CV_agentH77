from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app import models, schemas, auth
from app.database import get_db
from app.services.cv_parser import extract_text_from_pdf

router = APIRouter(prefix="/cv", tags=["cv"])


@router.get("", response_model=schemas.CVOut)
def get_my_cv(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    cv = db.query(models.CV).filter(models.CV.user_id == current_user.id).first()
    if not cv:
        raise HTTPException(status_code=404, detail="Aun no has subido tu CV")
    return cv


@router.put("", response_model=schemas.CVOut)
def upsert_cv_text(
    payload: schemas.CVUpsert,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """Crea o actualiza el CV a partir de texto (pegado directamente por el usuario)."""
    cv = db.query(models.CV).filter(models.CV.user_id == current_user.id).first()
    if cv:
        cv.raw_text = payload.raw_text
        cv.skills = payload.skills or []
        cv.summary = payload.summary
    else:
        cv = models.CV(
            user_id=current_user.id,
            raw_text=payload.raw_text,
            skills=payload.skills or [],
            summary=payload.summary,
        )
        db.add(cv)
    db.commit()
    db.refresh(cv)
    return cv


@router.post("/upload-pdf", response_model=schemas.CVOut)
async def upload_cv_pdf(
    file: UploadFile = File(...),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """Sube un PDF, extrae el texto automaticamente y lo guarda como CV."""
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Solo se acepta PDF")

    content = await file.read()
    text = extract_text_from_pdf(content)
    if not text:
        raise HTTPException(status_code=422, detail="No se pudo extraer texto del PDF (¿esta escaneado como imagen?)")

    cv = db.query(models.CV).filter(models.CV.user_id == current_user.id).first()
    if cv:
        cv.raw_text = text
    else:
        cv = models.CV(user_id=current_user.id, raw_text=text, skills=[])
        db.add(cv)
    db.commit()
    db.refresh(cv)
    return cv
