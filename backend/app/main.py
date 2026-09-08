"""
GymFit API — точка входа приложения.

Запуск (см. README.md в корне проекта):
    uvicorn app.main:app --reload --port 8000
"""
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routers import analytics, clients, subscriptions, visits, zones

# ---------------------- Логирование ----------------------
# Сюда BackgroundTasks из routers/visits.py пишут строки для аналитики,
# например: [INFO] Клиент Иванов Алексей успешно вошёл в зону «Бассейн» в 18:30
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "gymfit.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

# Создаём таблицы, если их ещё нет (на случай, если schema.sql не запускали отдельно)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="GymFit API",
    description="Учёт посещений и загруженности фитнес-клуба",
    version="1.0.0",
)

# Для локальной демки без Docker — открываем CORS всем источникам,
# чтобы frontend/index.html (открытый просто как файл) мог стучаться в API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(clients.router)
app.include_router(zones.router)
app.include_router(subscriptions.router)
app.include_router(visits.router)
app.include_router(analytics.router)


@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "GymFit API"}
