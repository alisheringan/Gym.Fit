from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/clients", tags=["Клиенты"])


@router.get("/", response_model=list[schemas.ClientOut])
def list_clients(db: Session = Depends(get_db)):
    """Список всех клиентов клуба."""
    return db.scalars(select(models.Client).order_by(models.Client.full_name)).all()


@router.post("/", response_model=schemas.ClientOut, status_code=201)
def create_client(payload: schemas.ClientCreate, db: Session = Depends(get_db)):
    """Добавить нового клиента."""
    client = models.Client(**payload.model_dump())
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@router.get("/{client_id}", response_model=schemas.ClientOut)
def get_client(client_id: int, db: Session = Depends(get_db)):
    client = db.get(models.Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    return client
