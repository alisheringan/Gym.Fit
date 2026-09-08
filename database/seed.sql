-- ============================================================
--  GymFit — тестовые данные (для демо аналитики)
-- ============================================================

-- ---------- Зоны ----------
INSERT INTO zones (name, description) VALUES
('Тренажерный зал', 'Зона со свободными весами и тренажёрами'),
('Кроссфит',        'Зал для функциональных тренировок'),
('Бассейн',         'Бассейн 25 м, 4 дорожки'),
('Йога',            'Зал для групповых занятий йогой'),
('Бокс',            'Зал для бокса и единоборств')
ON CONFLICT (name) DO NOTHING;

-- ---------- Клиенты ----------
INSERT INTO clients (full_name, phone, email) VALUES
('Иванов Алексей',    '+996700111201', 'ivanov@example.com'),
('Петрова Мария',     '+996700111202', 'petrova@example.com'),
('Сидоров Дмитрий',   '+996700111203', 'sidorov@example.com'),
('Кузнецова Анна',    '+996700111204', 'kuznetsova@example.com'),
('Смирнов Олег',      '+996700111205', 'smirnov@example.com'),
('Васильева Елена',   '+996700111206', 'vasilieva@example.com'),
('Новиков Артём',     '+996700111207', 'novikov@example.com'),
('Морозова Ольга',    '+996700111208', 'morozova@example.com'),
('Зайцев Игорь',      '+996700111209', 'zaytsev@example.com'),
('Орлова Светлана',   '+996700111210', 'orlova@example.com'),
('Беков Тимур',       '+996700111211', 'bekov@example.com'),    -- абонемент истёк
('Асанова Гульнара',  '+996700111212', 'asanova@example.com');  -- абонемент истёк

-- ---------- Абонементы ----------
-- Активные (action: end_date >= CURRENT_DATE) — клиенты id 1..10
INSERT INTO subscriptions (client_id, type, start_date, end_date)
SELECT id, 'Стандарт', CURRENT_DATE - INTERVAL '15 days', CURRENT_DATE + INTERVAL '15 days'
FROM clients WHERE id BETWEEN 1 AND 10;

-- Истёкшие — клиенты id 11, 12 (для проверки валидации в API)
INSERT INTO subscriptions (client_id, type, start_date, end_date)
SELECT id, 'Стандарт', CURRENT_DATE - INTERVAL '60 days', CURRENT_DATE - INTERVAL '5 days'
FROM clients WHERE id IN (11, 12);

-- ---------- Визиты за последние 60 дней ----------
-- Генерируем реалистичную нагрузку: больше людей по пн/ср/пт, меньше в выходные;
-- зоны распределены неравномерно (тренажёрный зал — самый популярный).
DO $$
DECLARE
    d              DATE;
    visits_today   INT;
    i              INT;
    client_count   INT;
    chosen_client  INT;
    chosen_zone    INT;
    r              DOUBLE PRECISION;
    visit_hour     INT;
    visit_minute   INT;
BEGIN
    SELECT COUNT(*) INTO client_count FROM clients;

    FOR d IN SELECT generate_series(CURRENT_DATE - INTERVAL '60 days', CURRENT_DATE - INTERVAL '1 day', INTERVAL '1 day')::date LOOP

        visits_today := CASE EXTRACT(ISODOW FROM d)
            WHEN 1 THEN 14 + floor(random() * 6)::int   -- понедельник — пик
            WHEN 2 THEN 8  + floor(random() * 4)::int
            WHEN 3 THEN 13 + floor(random() * 6)::int   -- среда — пик
            WHEN 4 THEN 8  + floor(random() * 4)::int
            WHEN 5 THEN 15 + floor(random() * 6)::int   -- пятница — пик
            WHEN 6 THEN 6  + floor(random() * 4)::int
            WHEN 7 THEN 4  + floor(random() * 3)::int
        END;

        FOR i IN 1..visits_today LOOP
            -- клиентов с истёкшим абонементом (11, 12) в реальные визиты не пускаем
            chosen_client := 1 + floor(random() * (client_count - 2))::int;

            r := random();
            chosen_zone := CASE
                WHEN r < 0.45 THEN 1   -- Тренажёрный зал
                WHEN r < 0.65 THEN 2   -- Кроссфит
                WHEN r < 0.80 THEN 3   -- Бассейн
                WHEN r < 0.92 THEN 4   -- Йога
                ELSE 5                  -- Бокс
            END;

            visit_hour   := 7 + floor(random() * 15)::int;  -- зал открыт 7:00–22:00
            visit_minute := floor(random() * 60)::int;

            INSERT INTO visits (client_id, zone_id, visit_time)
            VALUES (
                chosen_client,
                chosen_zone,
                d + (visit_hour || ' hours')::interval + (visit_minute || ' minutes')::interval
            );
        END LOOP;
    END LOOP;
END $$;
