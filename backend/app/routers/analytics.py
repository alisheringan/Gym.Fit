"""
Аналитические отчёты для администратора/владельца клуба:
  GET /analytics/zones        — популярность зон (визитов по зоне за период)
  GET /analytics/weekdays     — загруженность по дням недели
  GET /analytics/top-clients  — топ-N клиентов за месяц
"""
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..schemas import TopClient, WeekdayLoad, ZonePopularity

router = APIRouter(prefix="/analytics", tags=["Аналитика"])

WEEKDAY_NAMES = {
    1: "Понедельник",
    2: "Вторник",
    3: "Среда",
    4: "Четверг",
    5: "Пятница",
    6: "Суббота",
    7: "Воскресенье",
}


def _period_filters(date_from: Optional[date], date_to: Optional[date]):
    """date_to включительно — добавляем сутки, чтобы захватить весь день."""
    filters = []
    if date_from:
        filters.append(models.Visit.visit_time >= date_from)
    if date_to:
        filters.append(models.Visit.visit_time < date_to + timedelta(days=1))
    return filters


@router.get("/zones", response_model=list[ZonePopularity])
def zones_popularity(
    date_from: Optional[date] = Query(None, description="Начало периода (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="Конец периода (YYYY-MM-DD), включительно"),
    db: Session = Depends(get_db),
):
    """Сколько суммарно визитов было в каждую зону за период (GROUP BY зона, COUNT)."""
    query = (
        select(
            models.Zone.id.label("zone_id"),
            models.Zone.name.label("zone_name"),
            func.count(models.Visit.id).label("visits_count"),
        )
        .join(models.Visit, models.Visit.zone_id == models.Zone.id)
        .where(*_period_filters(date_from, date_to))
        .group_by(models.Zone.id, models.Zone.name)
        .order_by(func.count(models.Visit.id).desc())
    )
    rows = db.execute(query).all()
    return [ZonePopularity(**row._mapping) for row in rows]


@router.get("/weekdays", response_model=list[WeekdayLoad])
def weekday_load(
    date_from: Optional[date] = Query(None, description="Начало периода (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="Конец периода (YYYY-MM-DD), включительно"),
    db: Session = Depends(get_db),
):
    """В какие дни недели в зал приходит больше всего людей (для графика тренеров)."""
    weekday_expr = func.extract("isodow", models.Visit.visit_time).label("weekday_number")
    query = (
        select(weekday_expr, func.count(models.Visit.id).label("visits_count"))
        .where(*_period_filters(date_from, date_to))
        .group_by(weekday_expr)
        .order_by(weekday_expr)
    )
    rows = db.execute(query).all()
    return [
        WeekdayLoad(
            weekday_number=int(row.weekday_number),
            weekday_name=WEEKDAY_NAMES[int(row.weekday_number)],
            visits_count=row.visits_count,
        )
        for row in rows
    ]


@router.get("/top-clients", response_model=list[TopClient])
def top_clients(
    year: Optional[int] = Query(None, description="Год (по умолчанию — текущий)"),
    month: Optional[int] = Query(None, ge=1, le=12, description="Месяц 1-12 (по умолчанию — текущий)"),
    limit: int = Query(5, ge=1, le=50, description="Сколько клиентов показать (по умолчанию топ-5)"),
    db: Session = Depends(get_db),
):
    """Топ-N клиентов по количеству визитов за выбранный месяц."""
    today = date.today()
    target_year = year or today.year
    target_month = month or today.month

    query = (
        select(
            models.Client.id.label("client_id"),
            models.Client.full_name.label("client_name"),
            func.count(models.Visit.id).label("visits_count"),
        )
        .join(models.Visit, models.Visit.client_id == models.Client.id)
        .where(
            func.extract("year", models.Visit.visit_time) == target_year,
            func.extract("month", models.Visit.visit_time) == target_month,
        )
        .group_by(models.Client.id, models.Client.full_name)
        .order_by(func.count(models.Visit.id).desc())
        .limit(limit)
    )
    rows = db.execute(query).all()
    return [TopClient(**row._mapping) for row in rows]
