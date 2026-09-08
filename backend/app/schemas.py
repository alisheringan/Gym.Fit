"""
Pydantic-схемы: что принимает и что отдаёт API.
"""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


# ---------------------- Клиенты ----------------------
class ClientBase(BaseModel):
    full_name: str
    phone: Optional[str] = None
    email: Optional[str] = None

    @field_validator("phone", "email", mode="before")
    @classmethod
    def blank_to_none(cls, v):
        """Пустая строка из формы — это «не указано», а не значение."""
        if v is None:
            return None
        v = v.strip()
        return v or None


class ClientCreate(ClientBase):
    pass


class ClientOut(ClientBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


# ---------------------- Зоны ----------------------
class ZoneBase(BaseModel):
    name: str
    description: Optional[str] = None


class ZoneCreate(ZoneBase):
    pass


class ZoneOut(ZoneBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ---------------------- Абонементы ----------------------
class SubscriptionBase(BaseModel):
    client_id: int
    type: str = "Стандарт"
    start_date: date
    end_date: date


class SubscriptionCreate(SubscriptionBase):
    pass


class SubscriptionOut(SubscriptionBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


# ---------------------- Визиты ----------------------
class VisitCreate(BaseModel):
    client_id: int
    zone_id: int
    visit_time: Optional[datetime] = None  # если не указано — берётся текущее время


class VisitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    client_id: int
    zone_id: int
    visit_time: datetime


class VisitDetailOut(VisitOut):
    client_name: str
    zone_name: str


# ---------------------- Аналитика ----------------------
class ZonePopularity(BaseModel):
    zone_id: int
    zone_name: str
    visits_count: int


class WeekdayLoad(BaseModel):
    weekday_number: int
    weekday_name: str
    visits_count: int


class TopClient(BaseModel):
    client_id: int
    client_name: str
    visits_count: int
