# Midas Beta Testing - Admin Commands

## 📊 Мониторинг пользователей

### Удалить конкретного пользователя и его данные
```bash
# Замени TELEGRAM_ID
docker compose exec -T db psql -U postgres -d midas_db << 'EOF'
DELETE FROM users WHERE telegram_id = 2040216796;
SELECT 'User deleted!' as status;
EOF

### Список всех пользователей
```bash
docker compose exec -T db psql -U postgres -d midas_db -c "
SELECT 
    telegram_id,
    name,
    phone_number,
    created_at,
    default_currency
FROM users 
ORDER BY created_at DESC;
"
```

### Подробная информация о пользователе
```bash
# По telegram_id
docker compose exec -T db psql -U postgres -d midas_db -c "
SELECT * FROM users WHERE telegram_id = 867663387;
"

# По имени
docker compose exec -T db psql -U postgres -d midas_db -c "
SELECT * FROM users WHERE name ILIKE '%Komron%';
"
```

### Статистика пользователей
```bash
docker compose exec -T db psql -U postgres -d midas_db -c "
SELECT 
    COUNT(*) as total_users,
    COUNT(DISTINCT default_currency) as currencies_used,
    MIN(created_at) as first_user,
    MAX(created_at) as last_user
FROM users;
"
```

---

## 💰 Транзакции

### Транзакции конкретного пользователя
```bash
# Замени TELEGRAM_ID на нужный
docker compose exec -T db psql -U postgres -d midas_db << 'EOF'
SELECT 
    t.id,
    t.type,
    t.amount,
    t.currency,
    t.description,
    c.name as category,
    t.transaction_date,
    u.name as user_name
FROM transactions t
JOIN users u ON t.user_id = u.id
LEFT JOIN categories c ON t.category_id = c.id
WHERE u.telegram_id = 2040216796
ORDER BY t.transaction_date DESC
LIMIT 20;
EOF
```

### Все последние транзакции
```bash
docker compose exec -T db psql -U postgres -d midas_db -c "
SELECT 
    u.name as user,
    t.type,
    t.amount,
    t.description,
    c.name as category,
    t.transaction_date
FROM transactions t
JOIN users u ON t.user_id = u.id
LEFT JOIN categories c ON t.category_id = c.id
ORDER BY t.created_at DESC
LIMIT 30;
"
```

### Транзакции без категории
```bash
docker compose exec -T db psql -U postgres -d midas_db -c "
SELECT 
    u.name,
    t.description,
    t.amount,
    t.type,
    t.transaction_date
FROM transactions t
JOIN users u ON t.user_id = u.id
WHERE t.category_id IS NULL
ORDER BY t.created_at DESC;
"
```

### Статистика по пользователю
```bash
docker compose exec -T db psql -U postgres -d midas_db << 'EOF'
WITH user_stats AS (
    SELECT 
        u.name,
        u.telegram_id,
        COUNT(t.id) as total_transactions,
        SUM(CASE WHEN t.type = 'income' THEN t.amount ELSE 0 END) as total_income,
        SUM(CASE WHEN t.type = 'expense' THEN t.amount ELSE 0 END) as total_expense
    FROM users u
    LEFT JOIN transactions t ON u.id = t.user_id
    WHERE u.telegram_id = 2040216796
    GROUP BY u.id, u.name, u.telegram_id
)
SELECT 
    name,
    telegram_id,
    total_transactions,
    total_income,
    total_expense,
    (total_income - total_expense) as balance
FROM user_stats;
EOF
```

---

## 🏷️ Категории

### Популярные категории
```bash
docker compose exec -T db psql -U postgres -d midas_db -c "
SELECT 
    c.name,
    c.type,
    COUNT(t.id) as usage_count,
    SUM(t.amount) as total_amount
FROM categories c
LEFT JOIN transactions t ON c.id = t.category_id
GROUP BY c.id, c.name, c.type
ORDER BY usage_count DESC;
"
```

### Неиспользуемые категории
```bash
docker compose exec -T db psql -U postgres -d midas_db -c "
SELECT name, type 
FROM categories c
WHERE NOT EXISTS (
    SELECT 1 FROM transactions t WHERE t.category_id = c.id
)
ORDER BY type, name;
"
```

---

## 💸 Долги

### Все активные долги
```bash
docker compose exec -T db psql -U postgres -d midas_db -c "
SELECT 
    u.name as user,
    d.counterparty_name,
    d.amount,
    d.currency,
    d.type,
    d.is_settled,
    d.due_date,
    d.description
FROM debts d
JOIN users u ON d.user_id = u.id
ORDER BY d.created_at DESC;
"
```

### Неоплаченные долги
```bash
docker compose exec -T db psql -U postgres -d midas_db -c "
SELECT 
    u.name,
    d.counterparty_name,
    d.amount,
    d.type,
    d.due_date,
    d.description
FROM debts d
JOIN users u ON d.user_id = u.id
WHERE d.is_settled = false
ORDER BY d.due_date ASC;
"
```

---

## 🎯 Лимиты

### Лимиты пользователей
```bash
docker compose exec -T db psql -U postgres -d midas_db -c "
SELECT 
    u.name,
    c.name as category,
    l.amount as limit_amount,
    l.currency,
    l.period
FROM limits l
JOIN users u ON l.user_id = u.id
LEFT JOIN categories c ON l.category_id = c.id
ORDER BY u.name;
"
```

---

## 🧹 Очистка данных

### Удалить все данные (сохранить категории)
```bash
docker compose exec -T db psql -U postgres -d midas_db << 'EOF'
TRUNCATE TABLE transactions RESTART IDENTITY CASCADE;
TRUNCATE TABLE debts RESTART IDENTITY CASCADE;
TRUNCATE TABLE limits RESTART IDENTITY CASCADE;
TRUNCATE TABLE users RESTART IDENTITY CASCADE;
SELECT 'All data cleared!' as status;
EOF
```

### Удалить конкретного пользователя и его данные
```bash
# Замени TELEGRAM_ID
docker compose exec -T db psql -U postgres -d midas_db << 'EOF'
DELETE FROM users WHERE telegram_id = 867663387;
SELECT 'User deleted!' as status;
EOF
```

### Удалить старые транзакции
```bash
# Удалить транзакции старше 30 дней
docker compose exec -T db psql -U postgres -d midas_db -c "
DELETE FROM transactions 
WHERE transaction_date < NOW() - INTERVAL '30 days';
"
```

---

## 📈 Общая статистика

### Дашборд
```bash
docker compose exec -T db psql -U postgres -d midas_db << 'EOF'
SELECT 'Users' as metric, COUNT(*)::text as value FROM users
UNION ALL
SELECT 'Transactions', COUNT(*)::text FROM transactions
UNION ALL
SELECT 'Categories', COUNT(*)::text FROM categories
UNION ALL
SELECT 'Debts', COUNT(*)::text FROM debts
UNION ALL
SELECT 'Active Debts', COUNT(*)::text FROM debts WHERE is_settled = false
UNION ALL
SELECT 'Limits', COUNT(*)::text FROM limits;
EOF
```

### Активность за последние 7 дней
```bash
docker compose exec -T db psql -U postgres -d midas_db -c "
SELECT 
    DATE(created_at) as date,
    COUNT(*) as transactions
FROM transactions
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;
"
```

---

## 🔍 Отладка

### Проверка форматов телефонов
```bash
docker compose exec -T db psql -U postgres -d midas_db -c "
SELECT 
    telegram_id,
    name,
    phone_number,
    LENGTH(phone_number) as phone_length,
    CASE 
        WHEN phone_number ~ '^998[0-9]{9}$' THEN 'OK'
        ELSE 'BAD FORMAT'
    END as format_check
FROM users;
"
```

### Проверка дубликатов
```bash
docker compose exec -T db psql -U postgres -d midas_db -c "
-- Дубликаты telegram_id
SELECT telegram_id, COUNT(*) 
FROM users 
GROUP BY telegram_id 
HAVING COUNT(*) > 1;

-- Дубликаты phone
SELECT phone_number, COUNT(*) 
FROM users 
GROUP BY phone_number 
HAVING COUNT(*) > 1;
"
```

---

## 💾 Бэкап

### Создать дамп БД
```bash
docker compose exec -T db pg_dump -U postgres midas_db > midas_backup_$(date +%Y%m%d_%H%M%S).sql
```

### Восстановить из бэкапа
```bash
cat midas_backup_YYYYMMDD_HHMMSS.sql | docker compose exec -T db psql -U postgres -d midas_db
```

---

## 🎨 Полезные алиасы

Добавь в `~/.bashrc` или `~/.zshrc`:

```bash
# Midas shortcuts
alias midas-users='docker compose exec -T db psql -U postgres -d midas_db -c "SELECT telegram_id, name, phone_number FROM users ORDER BY created_at DESC;"'
alias midas-stats='docker compose exec -T db psql -U postgres -d midas_db -c "SELECT '\''Users'\'' as metric, COUNT(*)::text FROM users UNION ALL SELECT '\''Transactions'\'', COUNT(*)::text FROM transactions;"'
alias midas-logs='docker compose logs -f --tail=50'
alias midas-api-logs='docker compose logs -f api --tail=50'
alias midas-bot-logs='docker compose logs -f bot --tail=50'
```

Затем: `source ~/.bashrc` и используй короткие команды!


### Добавить категории
```bash
docker compose exec -T db psql -U postgres -d midas_db << 'EOF'
INSERT INTO categories (id, name, slug, type, icon, color, is_default) VALUES
(gen_random_uuid(), 'Еда', 'food', 'expense', '🍔', '#FF6B6B', true),
(gen_random_uuid(), 'Транспорт', 'transport', 'expense', '🚗', '#4ECDC4', true),
(gen_random_uuid(), 'Жильё', 'housing', 'expense', '🏠', '#95E1D3', true),
(gen_random_uuid(), 'Развлечения', 'entertainment', 'expense', '🎮', '#F38181', true),
(gen_random_uuid(), 'Здоровье', 'health', 'expense', '💊', '#AA96DA', true),
(gen_random_uuid(), 'Образование', 'education', 'expense', '📚', '#FCBAD3', true),
(gen_random_uuid(), 'Одежда', 'clothing', 'expense', '👔', '#A8D8EA', true),
(gen_random_uuid(), 'Связь', 'communication', 'expense', '📱', '#FFD93D', true),
(gen_random_uuid(), 'Подарки', 'gifts', 'expense', '🎁', '#6BCB77', true),
(gen_random_uuid(), 'Спорт', 'sports', 'expense', '⚽', '#4D96FF', true),
(gen_random_uuid(), 'Красота', 'beauty', 'expense', '💄', '#FDA7DF', true),
(gen_random_uuid(), 'Путешествия', 'travel', 'expense', '✈️', '#F6A5C0', true),
(gen_random_uuid(), 'Кафе', 'cafes', 'expense', '☕', '#F3D250', true),
(gen_random_uuid(), 'Продукты', 'groceries', 'expense', '🛒', '#90CCF4', true),
(gen_random_uuid(), 'Такси', 'taxi', 'expense', '🚕', '#F78888', true),
(gen_random_uuid(), 'Коммуналка', 'utilities', 'expense', '💡', '#5EAAA8', true),
(gen_random_uuid(), 'Другое', 'other_expense', 'expense', '💰', '#B8B5FF', true),
(gen_random_uuid(), 'Зарплата', 'salary', 'income', '💵', '#26de81', true),
(gen_random_uuid(), 'Фриланс', 'freelance', 'income', '💻', '#45aaf2', true),
(gen_random_uuid(), 'Инвестиции', 'investments', 'income', '📈', '#a55eea', true),
(gen_random_uuid(), 'Подарок', 'gift_income', 'income', '🎁', '#fd79a8', true),
(gen_random_uuid(), 'Другое', 'other_income', 'income', '💸', '#00b894', true)
ON CONFLICT DO NOTHING;

SELECT COUNT(*), type FROM categories GROUP BY type;
EOF
```

# Проверить количество категорий 
```bash
docker compose exec -T db psql -U postgres -d midas_db -c "SELECT COUNT(*), type FROM categories GROUP BY type ORDER BY type;"
```