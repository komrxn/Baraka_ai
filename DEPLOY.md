# 🚀 Production Deployment - Path-Based Routing

## Архитектура

```
http://your-ip/         → Существующий сервис (kkh)
http://your-ip/midas    → Midas Frontend
http://your-ip/midas-api → Midas API
```

Сервер nginx маршрутизирует запросы на Docker контейнеры на портах:
- Frontend: `localhost:3001`
- API: `localhost:8001`

---

## Deployment на сервере

### 1. Обновить код

```bash
cd /opt/Midas_ai
git pull
```

### 2. Добавить конфиг в server nginx

```bash
# Редактировать существующий конфиг
sudo nano /etc/nginx/sites-available/default

# Добавить location блоки из файла nginx.server.conf
# (см. содержимое файла ниже)

# Проверить конфиг
sudo nginx -t

# Перезагрузить nginx
sudo systemctl reload nginx
```

**Содержимое для добавления** (из `nginx.server.conf`):

```nginx
# Midas Frontend
location /midas/ {
    proxy_pass http://localhost:3001/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_cache_bypass $http_upgrade;
}

# Midas API
location /midas-api/ {
    rewrite ^/midas-api/(.*)$ /$1 break;
    proxy_pass http://localhost:8001;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    
    # CORS
    add_header Access-Control-Allow-Origin "*" always;
    add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
    add_header Access-Control-Allow-Headers "Authorization, Content-Type" always;
}
```

### 3. Запустить Docker сервисы

```bash
cd /opt/Midas_ai

# Остановить старые контейнеры
docker-compose down

# Собрать и запустить
docker-compose build --no-cache
docker-compose up -d

# Проверить статус
docker-compose ps
```

### 4. Проверить работу

```bash
# Frontend
curl http://localhost:3001

# API
curl http://localhost:8001/health

# Через nginx
curl http://localhost/midas
curl http://localhost/midas-api/health
```

---

## Доступ к сервисам

- **Frontend**: `http://your-server-ip/midas`
- **API Docs**: `http://your-server-ip/midas-api/docs`
- **API Health**: `http://your-server-ip/midas-api/health`

---

## Troubleshooting

### Nginx не перенаправляет

```bash
# Проверить конфиг
sudo nginx -t

# Логи nginx
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# Перезагрузить
sudo systemctl reload nginx
```

### Frontend показывает 404

```bash
# Проверить что контейнер работает
docker-compose ps frontend

# Проверить что порт открыт
curl http://localhost:3001

# Логи
docker-compose logs frontend
```

### API не отвечает

```bash
# Проверить контейнер
docker-compose ps api

# Проверить порт
curl http://localhost:8001/health

# Логи
docker-compose logs api
```

### CORS ошибки

В браузере F12 → Console, если видишь CORS ошибки:

```bash
# Добавь в nginx location /midas-api/:
add_header Access-Control-Allow-Origin "*" always;
```

---

## Полезные команды

```bash
# Логи всех сервисов
docker-compose logs -f

# Рестарт
docker-compose restart

# Пересборка после изменений
docker-compose build --no-cache
docker-compose up -d

# Остановить всё
docker-compose down

# Удалить volumes (ОСТОРОЖНО!)
docker-compose down -v
```

---

## Backup БД

```bash
# Создать backup
docker-compose exec db pg_dump -U postgres midas_db > backup_$(date +%Y%m%d).sql

# Восстановить
docker-compose exec -T db psql -U postgres midas_db < backup_20241216.sql
```

---

## Обновление при изменениях

```bash
# Стандартное обновление
cd /opt/Midas_ai
git pull
docker-compose build
docker-compose up -d

# Если изменили docker-compose.yml
docker-compose down
docker-compose up -d
```
