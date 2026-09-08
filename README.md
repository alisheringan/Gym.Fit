# GymFit — учёт посещений фитнес-клуба

Backend на FastAPI + PostgreSQL, фронтенд — обычный HTML/CSS/JS без сборки.
**Без Docker.** Два процесса: backend на 8000-м порту, фронтенд — просто открытый файл (или любой статический сервер).

## Структура проекта

```
gymfit/
├── backend/
│   ├── app/
│   │   ├── main.py            — точка входа FastAPI
│   │   ├── database.py        — подключение к Postgres
│   │   ├── models.py          — ORM-модели (SQLAlchemy)
│   │   ├── schemas.py         — Pydantic-схемы запросов/ответов
│   │   └── routers/           — clients, zones, subscriptions, visits, analytics
│   ├── requirements.txt
│   └── .env.example
├── database/
│   ├── schema.sql              — таблицы и индексы
│   └── seed.sql                — тестовые клиенты/зоны/визиты
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
└── README.md
```

## 1. PostgreSQL

Нужен установленный Postgres (локально, без Docker).

```bash
sudo apt install postgresql      # если ещё не установлен
sudo systemctl start postgresql
sudo systemctl enable postgresql # чтобы поднимался сам при загрузке системы
```

Создаём пользователя и базу:

```bash
sudo -u postgres psql -c "CREATE USER gymfit_user WITH PASSWORD 'gymfit_pass';"
sudo -u postgres psql -c "CREATE DATABASE gymfit OWNER gymfit_user;"
```

Накатываем схему и тестовые данные:

```bash
cd database
PGPASSWORD=gymfit_pass psql -h localhost -U gymfit_user -d gymfit -f schema.sql
PGPASSWORD=gymfit_pass psql -h localhost -U gymfit_user -d gymfit -f seed.sql
```

`seed.sql` создаёт 5 зон, 12 клиентов (10 с активным абонементом, 2 — с истёкшим, чтобы
сразу проверить валидацию) и ~700 визитов за последние 60 дней с реалистичным
распределением по дням недели и зонам — отчёты сразу будут с чем работать.

## 2. Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

`.env` создавать не обязательно — дефолтный `DATABASE_URL` в `app/database.py` уже
смотрит на `gymfit_user:gymfit_pass@localhost:5432/gymfit`. Если у вас другие
креды — скопируйте `.env.example` в `.env` и поправьте строку подключения.

Проверка, что всё поднялось:

```bash
curl http://localhost:8000/
# {"status":"ok","service":"GymFit API"}
```

Документация API (Swagger) — автоматически на `http://localhost:8000/docs`.

## 3. Frontend

Никакой сборки не требуется — это обычные `.html`/`.css`/`.js`.

Самый простой способ — открыть `frontend/index.html` прямо в браузере двойным
кликом. Backend разрешает запросы с любого источника (CORS `*`), так что это
будет работать даже при открытии файла напрямую (`file://`).

Если предпочитаете через локальный сервер (избегает редких квирков браузера
с `file://`):

```bash
cd frontend
python3 -m http.server 5500
```

и открыть `http://localhost:5500`.

> Если backend крутится не на `localhost:8000`, поменяйте константу
> `API_BASE` в начале `frontend/app.js`.

## Бизнес-логика

- **Регистрация визита** (`POST /visits/`) — перед записью визита проверяется,
  есть ли у клиента абонемент с `end_date >= текущая дата`. Если нет — `403` и
  визит не создаётся.
- **Фоновая аналитика** — при успешной регистрации визита `BackgroundTasks`
  пишет строку в `backend/logs/gymfit.log`, не задерживая ответ клиенту.
- **Отчёты** (`GET /analytics/...`):
  - `/analytics/zones` — популярность зон за период (`date_from`, `date_to`)
  - `/analytics/weekdays` — загруженность по дням недели за период
  - `/analytics/top-clients` — топ-N клиентов за месяц (`year`, `month`, `limit`)

## Если что-то не заводится

- **`connection refused` / нет соединения с БД** — проверьте `sudo systemctl status postgresql`.
- **`password authentication failed`** — пересоздайте пользователя:
  `sudo -u postgres psql -c "ALTER USER gymfit_user WITH PASSWORD 'gymfit_pass';"`
- **Порт 8000 занят** — запустите на другом порту (`--port 8001`) и поменяйте
  `API_BASE` в `app.js`.
- **Фронт не видит backend** — откройте консоль браузера (F12), там будет
  точная причина (обычно — backend просто не запущен).
