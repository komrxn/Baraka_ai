# 🚀 Midas AI Accountant - Deployment Guide

## Полная инструкция по развертыванию на сервере

---

## 📋 Что будет развернуто

1. **PostgreSQL** - база данных
2. **FastAPI** - API backend
3. **Telegram Bot** - AI-агент с Function Calling
4. **Nginx** (опционально) - reverse proxy

---

## 🛠 Требования к серверу

### Минимальные характеристики:
- **OS**: Ubuntu 20.04+ / Debian 11+
- **RAM**: 2GB минимум (4GB рекомендуется для AI)
- **CPU**: 2 cores
- **Disk**: 20GB
- **Порты**: 80, 443 (Nginx), 8001 (API)

### Необходимое ПО:
```bash
# Docker
# Docker Compose
# Git
```

---

## 📦 Шаг 1: Подготовка сервера

### 1.1 Подключитесь к серверу
```bash
ssh user@your-server-ip
```

### 1.2 Обновите систему
```bash
sudo apt update && sudo apt upgrade -y
```

### 1.3 Установите Docker
```bash
# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Добавление пользователя в группу docker
sudo usermod -aG docker $USER

# Перезайдите в систему или выполните:
newgrp docker

# Проверка
docker --version
```

### 1.4 Установите Docker Compose
```bash
# Docker Compose обычно идет с Docker Desktop
# Если нет, установите:
sudo apt install docker-compose-plugin -y

# Проверка
docker compose version
```

### 1.5 Установите Git
```bash
sudo apt install git -y
```

---

## 📂 Шаг 2: Клонирование проекта

```bash
# Создайте директорию для проекта
mkdir -p ~/apps
cd ~/apps

# Клонируйте репозиторий
git clone https://github.com/YOUR_USERNAME/midas.git
cd midas
```

---

## 🔐 Шаг 3: Настройка переменных окружения

### 3.1 Создайте .env файл
```bash
cp .env.example .env
nano .env
```

### 3.2 Заполните критические переменные

```bash
# =============================================================================
# Midas AI - Production Configuration
# =============================================================================

# Database Configuration
POSTGRES_DB=midas_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=YOUR_SECURE_PASSWORD_HERE  # ← ИЗМЕНИТЕ!
POSTGRES_PORT=5432

# API Configuration
API_PORT=8001

# JWT Authentication
SECRET_KEY=GENERATE_RANDOM_SECRET_KEY_HERE  # ← СГЕНЕРИРУЙТЕ!
ACCESS_TOKEN_EXPIRE_MINUTES=43200

# OpenAI API
OPENAI_API_KEY=sk-proj-YOUR_OPENAI_KEY_HERE  # ← ВАШ КЛЮЧ!

# CORS (если есть фронтенд)
CORS_ORIGINS=https://yourdomain.com

# Nginx (опционально)
NGINX_PORT=80
NGINX_SSL_PORT=443

# Internal Database URL (не трогайте, используется Docker)
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_SECURE_PASSWORD_HERE@db:5432/midas_db

# Telegram Bot
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_FROM_BOTFATHER  # ← ТОКЕН БОТА!
API_BASE_URL=http://api:8000
```

### 3.3 Генерация SECRET_KEY
```bash
# Сгенерируйте случайный ключ
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Скопируйте результат в SECRET_KEY
```

### 3.4 Получение Telegram Bot Token
```bash
# 1. Откройте Telegram
# 2. Найдите @BotFather
# 3. Отправьте /newbot
# 4. Следуйте инструкциям
# 5. Скопируйте токен вида: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz
# 6. Вставьте в TELEGRAM_BOT_TOKEN
```

---

## 🏗 Шаг 4: Запуск проекта

### 4.1 Соберите и запустите контейнеры
```bash
# Сборка образов
docker compose build

# Запуск всех сервисов
docker compose up -d

# Проверка статуса
docker compose ps
```

**Должны быть запущены:**
- `midas_postgres` (PostgreSQL)
- `midas_api` (FastAPI)
- `midas_bot` (Telegram Bot)

### 4.2 Проверка логов
```bash
# Логи API
docker compose logs api -f

# Логи бота
docker compose logs bot -f

# Логи базы данных
docker compose logs db -f

# Все логи сразу
docker compose logs -f
```

### 4.3 Ожидаемые логи при успешном запуске

**API:**
```
INFO - 🚀 Starting AI Accountant API...
INFO - ✅ Database initialized
INFO - Application startup complete
```

**Bot:**
```
INFO - 🤖 Starting Midas Telegram Bot...
INFO - Application started
```

---

## ✅ Шаг 5: Проверка работоспособности

### 5.1 Проверка API
```bash
# Health check
curl http://localhost:8001/health

# Должен вернуть: {"status":"healthy"}
```

### 5.2 Проверка бота
```bash
# Откройте Telegram
# Найдите вашего бота по username
# Отправьте /start
# Бот должен ответить
```

### 5.3 Тестирование функциональности
```bash
# В боте попробуйте:
# 1. /start - регистрация
# 2. "Потратил на кофе 25000" - создание транзакции
# 3. 💰 Баланс - проверка баланса
# 4. 📊 Статистика - статистика по категориям
```

---

## 🔒 Шаг 6: Настройка Nginx (опционально, для HTTPS)

### 6.1 Создайте SSL сертификаты с Let's Encrypt
```bash
# Установите certbot
sudo apt install certbot python3-certbot-nginx -y

# Получите сертификат
sudo certbot --nginx -d yourdomain.com -d api.yourdomain.com
```

### 6.2 Запустите Nginx
```bash
# Активируйте Nginx в docker-compose
docker compose --profile production up -d nginx
```

### 6.3 Обновите CORS_ORIGINS
```bash
# В .env добавьте ваш домен
CORS_ORIGINS=https://yourdomain.com,https://api.yourdomain.com
```

---

## 🔄 Управление проектом

### Остановка всех сервисов
```bash
docker compose down
```

### Restart сервисов
```bash
docker compose restart
```

### Restart конкретного сервиса
```bash
docker compose restart api
docker compose restart bot
```

### Обновление кода
```bash
# Pull новых изменений
git pull

# Пересоберите и перезапустите
docker compose build
docker compose up -d
```

### Просмотр логов
```bash
# Все логи
docker compose logs -f

# Логи конкретного сервиса
docker compose logs api -f
docker compose logs bot -f
```

### Очистка старых образов
```bash
docker system prune -a
```

---

## 📊 Мониторинг

### Проверка использования ресурсов
```bash
# Использование контейнерами
docker stats

# Использование дисками
df -h

# Использование памятью
free -h
```

---

## 🐛 Troubleshooting

### Проблема: Bot не запускается
**Решение:**
```bash
# Проверьте логи
docker compose logs bot

# Убедитесь что API запущен
curl http://localhost:8001/health

# Проверьте TELEGRAM_BOT_TOKEN в .env
```

### Проблема: API возвращает 500 ошибки
**Решение:**
```bash
# Логи API
docker compose logs api -f

# Проверка подключения к БД
docker compose exec db psql -U postgres -d midas_db -c "SELECT 1;"

# Проверка DATABASE_URL в .env
```

### Проблема: База данных не инициализируется
**Решение:**
```bash
# Остановите все
docker compose down -v

# Удалите volume
docker volume rm midas_postgres_data

# Запустите заново
docker compose up -d
```

### Проблема: OpenAI API timeout
**Решение:**
```bash
# Проверьте OPENAI_API_KEY
# Проверьте интернет-соединение сервера
ping api.openai.com

# Увеличен timeout до 60 секунд в bot/ai_agent.py
```

---

## 🔐 Безопасность

### Рекомендации:

1. **Никогда не коммитьте .env в Git**
   ```bash
   # .env уже в .gitignore
   ```

2. **Используйте сильные пароли**
   ```bash
   # Сгенерируйте случайный пароль для БД
   openssl rand -base64 32
   ```

3. **Ограничьте доступ к портам**
   ```bash
   # Откройте только нужные порты через firewall
   sudo ufw allow 80
   sudo ufw allow 443
   sudo ufw enable
   ```

4. **Регулярно обновляйте систему**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

5. **Бэкапьте базу данных**
   ```bash
   # Создание бэкапа
   docker compose exec db pg_dump -U postgres midas_db > backup_$(date +%Y%m%d).sql

   # Восстановление
   docker compose exec -T db psql -U postgres midas_db < backup_20231215.sql
   ```

---

## 📝 Полезные команды

```bash
# Перезапуск всех сервисов
docker compose restart

# Просмотр запущенных контейнеров
docker ps

# Зайти в контейнер API
docker compose exec api bash

# Зайти в контейнер БД
docker compose exec db psql -U postgres -d midas_db

# Просмотр переменных окружения
docker compose config

# Остановка и удаление всего (включая volumes)
docker compose down -v
```

---

## ✅ Checklist развертывания

- [ ] Сервер подготовлен (Docker, Docker Compose установлены)
- [ ] Проект склонирован
- [ ] .env настроен с реальными ключами
- [ ] SECRET_KEY сгенерирован
- [ ] POSTGRES_PASSWORD изменен
- [ ] OPENAI_API_KEY добавлен
- [ ] TELEGRAM_BOT_TOKEN получен от @BotFather
- [ ] `docker compose build` выполнен успешно
- [ ] `docker compose up -d` запустил все сервисы
- [ ] API отвечает на /health
- [ ] Бот отвечает на /start в Telegram
- [ ] Транзакции создаются корректно
- [ ] Баланс и статистика работают
- [ ] Nginx настроен (если нужен HTTPS)
- [ ] Firewall настроен
- [ ] Бэкапы настроены

---

## 🎉 Готово!

Ваш Midas AI Accountant развернут и работает!

**Что дальше:**
- Настройте регулярные бэкапы БД
- Настройте мониторинг (Prometheus + Grafana)
- Добавьте фронтенд (если планируется)

**Поддержка:**
- GitHub Issues: https://github.com/YOUR_USERNAME/midas/issues
- Документация API: http://your-server:8001/docs
