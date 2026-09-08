"""
Подключение к PostgreSQL и фабрика сессий SQLAlchemy.
Строка подключения берётся из переменной окружения DATABASE_URL (см. .env.example).
"""
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://gymfit_user:gymfit_pass@localhost:5432/gymfit",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency для FastAPI: одна сессия БД на один запрос."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
