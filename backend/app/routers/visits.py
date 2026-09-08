"""
Регистрация визита клиента в зону.

Бизнес-логика:
1. Проверяем, что клиент и зона существуют.
2. Проверяем абонемент: ищем подписку клиента, у которой end_date >= текущей даты.
   Если активного абонемента нет — отдаём 403 и визит не создаём.
3. Создаём визит.
4. Запускаем фоновую задачу (BackgroundTasks) — она пишет строку в лог
   приложения для последующей аналитики, не задерживая ответ клиенту.
"""
import logging
from datetime import date, datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/visits", tags=["Визиты"])
logger = logging.getLogger("gymfit.analytics")


def log_visit_for_analytics(client_name: str, zone_name: str, visit_time: datetime) -> None:
    """Фоновая задача: пишем строку в лог приложения (см. logs/gymfit.log)."""
    logger.info(
        "Клиент %s успешно вошёл в зону «%s» в %s",
        client_name,
        zone_name,
        visit_time.strftime("%d.%m.%Y %H:%M"),
    )


@router.post("/", response_model=schemas.VisitDetailOut, status_code=201)
def register_visit(
    payload: schemas.VisitCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    client = db.get(models.Client, payload.client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")

    zone = db.get(models.Zone, payload.zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Зона не найдена")

    # --- Проверка абонемента (end_date >= текущая дата) ---
    active_sub = db.scalar(
        select(models.Subscription)
        .where(
            models.Subscription.client_id == payload.client_id,
            models.Subscription.end_date >= func.current_date(),
        )
        .order_by(models.Subscription.end_date.desc())
    )
    if not active_sub:
        raise HTTPException(
            status_code=403,
            detail=f"Абонемент клиента «{client.full_name}» истёк или не найден. Вход запрещён.",
        )

    visit_time = payload.visit_time or datetime.now()
    visit = models.Visit(client_id=client.id, zone_id=zone.id, visit_time=visit_time)
    db.add(visit)
    db.commit()
    db.refresh(visit)

    # --- Фоновая задача: не блокирует ответ администратору ---
    background_tasks.add_task(log_visit_for_analytics, client.full_name, zone.name, visit_time)

    return schemas.VisitDetailOut(
        id=visit.id,
        client_id=visit.client_id,
        zone_id=visit.zone_id,
        visit_time=visit.visit_time,
        client_name=client.full_name,
        zone_name=zone.name,
    )


@router.get("/", response_model=list[schemas.VisitDetailOut])
def list_visits(
    limit: int = 50,
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
):
    """
    Последние визиты (для журнала на вкладке «Регистрация»), либо все визиты
    за период (date_from/date_to, включительно) — используется календарём
    на вкладке «Календарь».
    """
    query = (
        select(
            models.Visit.id,
            models.Visit.client_id,
            models.Visit.zone_id,
            models.Visit.visit_time,
            models.Client.full_name.label("client_name"),
            models.Zone.name.label("zone_name"),
        )
        .join(models.Client, models.Client.id == models.Visit.client_id)
        .join(models.Zone, models.Zone.id == models.Visit.zone_id)
    )
    if date_from:
        query = query.where(models.Visit.visit_time >= date_from)
    if date_to:
        query = query.where(models.Visit.visit_time < date_to + timedelta(days=1))

    query = query.order_by(models.Visit.visit_time.desc()).limit(limit)
    rows = db.execute(query).all()
    return [schemas.VisitDetailOut(**row._mapping) for row in rows]
