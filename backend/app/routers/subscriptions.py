from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/subscriptions", tags=["Абонементы"])


@router.post("/", response_model=schemas.SubscriptionOut, status_code=201)
def create_subscription(payload: schemas.SubscriptionCreate, db: Session = Depends(get_db)):
    """Выдать клиенту новый абонемент."""
    client = db.get(models.Client, payload.client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    sub = models.Subscription(**payload.model_dump())
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


@router.get("/client/{client_id}", response_model=list[schemas.SubscriptionOut])
def list_client_subscriptions(client_id: int, db: Session = Depends(get_db)):
    """История абонементов конкретного клиента."""
    return db.scalars(
        select(models.Subscription)
        .where(models.Subscription.client_id == client_id)
        .order_by(models.Subscription.end_date.desc())
    ).all()
