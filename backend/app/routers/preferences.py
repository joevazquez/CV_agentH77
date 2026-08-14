from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas, auth
from app.database import get_db

router = APIRouter(prefix="/preferences", tags=["preferences"])


@router.get("", response_model=schemas.PreferenceOut)
def get_my_preferences(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    prefs = db.query(models.Preference).filter(models.Preference.user_id == current_user.id).first()
    if not prefs:
        raise HTTPException(status_code=404, detail="Aun no has configurado tus preferencias")
    return prefs


@router.put("", response_model=schemas.PreferenceOut)
def upsert_preferences(
    payload: schemas.PreferenceUpsert,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    prefs = db.query(models.Preference).filter(models.Preference.user_id == current_user.id).first()
    if prefs:
        for field, value in payload.model_dump().items():
            setattr(prefs, field, value)
    else:
        prefs = models.Preference(user_id=current_user.id, **payload.model_dump())
        db.add(prefs)
    db.commit()
    db.refresh(prefs)
    return prefs
