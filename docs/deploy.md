## Деплой: Accountant Bot (Telegram)

Ниже — пошаговая, минимальная и надёжная схема развёртывания на сервере под `/opt`. Бот работает по long polling — входящие порты открывать не нужно.

### 1) Предустановки (Ubuntu/Debian)

```bash
apt update
apt install -y git python3 python3-venv python3-pip
# Локальный Redis (можно пропустить, если используете управляемый Redis URI)
apt install -y redis-server
systemctl enable --now redis-server

# Проверьте, что Python ≥ 3.11
python3 --version
```

Если версия Python < 3.11 — установите более новый Python (или используйте дистрибутив с 3.11+).

### 2) Каталог проекта под /opt

```bash
cd /opt
git clone https://example.com/your/accountant-bot.git
cd accountant-bot
```

Опционально: запускать под отдельным пользователем (рекомендуется)

```bash
useradd -r -s /usr/sbin/nologin bot || true
chown -R bot:bot /opt/accountant-bot
```

### 3) Виртуальное окружение и зависимости

```bash
cd /opt/accountant-bot
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

### 4) Переменные окружения (.env)

Создайте `/opt/accountant-bot/.env` со значениями (без кавычек):

```bash
cat >/opt/accountant-bot/.env << 'EOF'
TELEGRAM_BOT_TOKEN=ВАШ_TELEGRAM_API_TOKEN
OPENAI_API_KEY=ВАШ_OPENAI_API_KEY
SUPABASE_URL=https://YOUR-PROJECT.supabase.co
SUPABASE_ANON_KEY=ВАШ_SUPABASE_ANON_KEY
REDIS_URL=redis://127.0.0.1:6379/0
DEFAULT_CURRENCY=uzs
EOF
```

Приложение автоматически читает `.env`. Если используете управляемый Redis — укажите соответствующий `REDIS_URL`.

### 5) Supabase схема (однократно)

Откройте Supabase SQL Editor и выполните SQL из `README.md` (раздел «Supabase SQL (one-shot)»). Будут созданы таблицы `expenses` и `user_settings`.

### 6) Пробный запуск (в консоли)

```bash
cd /opt/accountant-bot
source .venv/bin/activate
python -m app.main
```

Отправьте боту команду `/health` в Telegram — вы увидите статусы OpenAI/Redis/Supabase. Остановите Ctrl+C.

### 7) systemd-сервис

Создайте `/etc/systemd/system/accountant-bot.service`:

```ini
[Unit]
Description=Accountant Telegram Bot
After=network-online.target
Wants=network-online.target

[Service]
# По умолчанию запустим от root. Если создали пользователя 'bot' — поменяйте на User=bot
User=root
WorkingDirectory=/opt/accountant-bot
Environment=PYTHONUNBUFFERED=1
EnvironmentFile=/opt/accountant-bot/.env
ExecStart=/opt/accountant-bot/.venv/bin/python -m app.main
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Включение и запуск:

```bash
systemctl daemon-reload
systemctl enable --now accountant-bot
systemctl status accountant-bot --no-pager
journalctl -u accountant-bot -f
```

### 8) Обновление версии

```bash
cd /opt/accountant-bot
# если используете выделенного пользователя:
# sudo -u bot git pull --rebase
# sudo -u bot /opt/accountant-bot/.venv/bin/pip install -r requirements.txt
git pull --rebase
/opt/accountant-bot/.venv/bin/pip install -r requirements.txt
systemctl restart accountant-bot
```

### 9) Откат

```bash
cd /opt/accountant-bot
git log --oneline -n 10
git checkout <commit>
systemctl restart accountant-bot
```

### 10) Диагностика

- Команда `/health` в Telegram покажет состояние зависимостей.
- Логи: `journalctl -u accountant-bot -n 200 --no-pager` или `-f` для tail.
- Redis: `redis-cli ping` → PONG; иначе проверьте `REDIS_URL`.
- Supabase: проверьте `SUPABASE_URL` и `SUPABASE_ANON_KEY`.
- OpenAI: убедитесь, что `OPENAI_API_KEY` валиден и есть доступ к моделям в коде.

### Примечания

- Входящих портов не требуется (long polling).
- Таймзона сервера не критична для хранения (Supabase хранит timestamptz).

### Docker / Docker Compose

Вариант A (рекомендуется): Docker Compose с локальным Redis

1) Убедитесь, что `.env` заполнен. Для Compose используйте `REDIS_URL=redis://redis:6379/0`.
2) Запустите:

```bash
docker compose up -d --build
docker compose logs -f bot
```

Обновление:

```bash
docker compose pull || true
docker compose up -d --build bot
```

Остановка и удаление:

```bash
docker compose down
```

Вариант B: Один контейнер (внешний/хостовый Redis)

```bash
docker build -t accountant-bot:latest .
# Если Redis на хосте Linux:
#   добавьте маршрут host.docker.internal → host-gateway ИЛИ используйте --network host
docker run -d \
  --name accountant-bot \
  --restart unless-stopped \
  --env-file .env \
  --add-host=host.docker.internal:host-gateway \
  accountant-bot:latest
```

Примечание: Для одиночного контейнера при использовании Redis на хосте выставьте в `.env` `REDIS_URL=redis://host.docker.internal:6379/0` (на Linux требуется ключ `--add-host`, см. пример выше). Либо используйте `--network host`.

