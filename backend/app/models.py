"""
ORM-модели GymFit: клиенты, зоны, абонементы, визиты.
Структура зеркалит database/schema.sql.
"""
from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from .database import Base


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(150), nullable=False)
    phone = Column(String(20))
    email = Column(String(150))
    created_at = Column(DateTime, server_default=func.now())

    subscriptions = relationship(
        "Subscription", back_populates="client", cascade="all, delete-orphan"
    )
    visits = relationship("Visit", back_populates="client", cascade="all, delete-orphan")


class Zone(Base):
    __tablename__ = "zones"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(255))

    visits = relationship("Visit", back_populates="zone", cascade="all, delete-orphan")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(50), nullable=False, default="Стандарт")
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    client = relationship("Client", back_populates="subscriptions")


class Visit(Base):
    __tablename__ = "visits"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    zone_id = Column(Integer, ForeignKey("zones.id", ondelete="CASCADE"), nullable=False)
    visit_time = Column(DateTime, server_default=func.now())

    client = relationship("Client", back_populates="visits")
    zone = relationship("Zone", back_populates="visits")
