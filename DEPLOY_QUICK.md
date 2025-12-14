# 🚀 Quick Deployment Guide

## 1️⃣ Подготовка сервера (5 минут)

```bash
# Обновите систему
sudo apt update && sudo apt upgrade -y

# Установите Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
newgrp docker

# Установите Git
sudo apt install git -y
```

## 2️⃣ Клонирование проекта (1 минута)

```bash
cd ~/apps
git clone https://github.com/YOUR_USERNAME/midas.git
cd midas
```

## 3️⃣ Настройка .env (3 минуты)

```bash
cp .env.example .env
nano .env
```

**Измените эти переменные:**
```bash
POSTGRES_PASSWORD=YOUR_SECURE_PASSWORD  # ← Придумайте сложный пароль
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")  # ← Сгенерируйте
OPENAI_API_KEY=sk-proj-YOUR_KEY  # ← Ваш ключ от OpenAI
TELEGRAM_BOT_TOKEN=123456789:ABC...  # ← Получите у @BotFather в Telegram
```

## 4️⃣ Запуск (2 минуты)

```bash
# Сборка и запуск
docker compose build
docker compose up -d

# Проверка
docker compose ps
docker compose logs -f
```

## 5️⃣ Тестирование (1 минута)

```bash
# API здоровье
curl http://localhost:8001/health

# Telegram бот
# Откройте бота в Telegram и отправьте /start
```

---

## ✅ Готово! Всего 12 минут

**Обновление кода:**
```bash
cd ~/apps/midas
git pull
docker compose build
docker compose up -d
```

**Просмотр логов:**
```bash
docker compose logs bot -f  # Логи бота
docker compose logs api -f  # Логи API
```

**Restart:**
```bash
docker compose restart
```

---

📖 **Полная инструкция:** см. DEPLOYMENT_FULL.md
