from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/zones", tags=["Зоны"])


@router.get("/", response_model=list[schemas.ZoneOut])
def list_zones(db: Session = Depends(get_db)):
    """Список зон/групповых занятий клуба (Тренажёрный зал, Кроссфит, Бассейн и т.д.)."""
    return db.scalars(select(models.Zone).order_by(models.Zone.name)).all()


@router.post("/", response_model=schemas.ZoneOut, status_code=201)
def create_zone(payload: schemas.ZoneCreate, db: Session = Depends(get_db)):
    """Добавить новую зону."""
    exists = db.scalar(select(models.Zone).where(models.Zone.name == payload.name))
    if exists:
        raise HTTPException(status_code=400, detail="Зона с таким названием уже существует")
    zone = models.Zone(**payload.model_dump())
    db.add(zone)
    db.commit()
    db.refresh(zone)
    return zone
