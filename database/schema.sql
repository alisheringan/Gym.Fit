-- ============================================================
--  GymFit — схема базы данных (PostgreSQL)
--  Учёт посещений и загруженности фитнес-клуба
-- ============================================================

-- Клиенты клуба
CREATE TABLE IF NOT EXISTS clients (
    id          SERIAL PRIMARY KEY,
    full_name   VARCHAR(150) NOT NULL,
    phone       VARCHAR(20),
    email       VARCHAR(150),
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Зоны / групповые занятия (Тренажёрный зал, Кроссфит, Бассейн, ...)
CREATE TABLE IF NOT EXISTS zones (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(255)
);

-- Абонементы клиентов
CREATE TABLE IF NOT EXISTS subscriptions (
    id          SERIAL PRIMARY KEY,
    client_id   INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    type        VARCHAR(50) NOT NULL DEFAULT 'Стандарт',
    start_date  DATE NOT NULL,
    end_date    DATE NOT NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Визиты — фактические посещения клиентами зон
CREATE TABLE IF NOT EXISTS visits (
    id          SERIAL PRIMARY KEY,
    client_id   INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    zone_id     INTEGER NOT NULL REFERENCES zones(id) ON DELETE CASCADE,
    visit_time  TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Индексы под аналитические запросы (GROUP BY зоне / дате / клиенту)
CREATE INDEX IF NOT EXISTS idx_visits_zone         ON visits(zone_id);
CREATE INDEX IF NOT EXISTS idx_visits_client        ON visits(client_id);
CREATE INDEX IF NOT EXISTS idx_visits_time          ON visits(visit_time);
CREATE INDEX IF NOT EXISTS idx_subscriptions_client ON subscriptions(client_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_dates  ON subscriptions(end_date);
