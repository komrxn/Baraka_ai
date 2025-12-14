# 🚀 Production Deployment Guide

Step-by-step guide for deploying Midas API to production server.

---

## 📋 Prerequisites

- Server with Ubuntu 20.04+ or similar
- Docker & Docker Compose installed
- Git installed
- OpenAI API key

---

## 🔧 Deployment Steps

### 1. SSH to Server

```bash
ssh user@your-server.com
```

### 2. Clone Repository

```bash
git clone https://github.com/yourusername/midas.git
cd midas
```

### 3. Create Environment File

```bash
cp env.production.example .env
nano .env
```

### 4. Configure Environment Variables

Edit `.env` file:

```bash
# Generate secure secret (run this first)
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Then set in .env:
SECRET_KEY=paste-generated-key-here
POSTGRES_PASSWORD=create-strong-password
OPENAI_API_KEY=sk-proj-your-key-here
CORS_ORIGINS=https://yourdomain.com
API_PORT=8000
```

### 5. Deploy

```bash
# First time deployment
docker compose up -d --build

# Check status
docker compose ps

# Should show both containers as "Up (healthy)"
```

### 6. Verify

```bash
# Test health
curl http://localhost:8000/health

# Expected: {"status":"healthy","database":"connected"}

# View logs
docker compose logs -f api
```

### 7. Test API

```bash
# Open Swagger docs
http://your-server:8000/docs

# Register first user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","email":"admin@test.com","password":"admin123"}'
```

✅ **Deployment Complete!** API running on port 8000

---

## � Updates

### Update to Latest Version

```bash
cd midas
git pull
docker compose down
docker compose up -d --build
```

### If Database Schema Changed

```bash
# CAUTION: This deletes all data!
docker compose down
docker volume rm midas_postgres_data
docker compose up -d --build
```

---

## 🔐 HTTPS Setup (Optional)

### Using Certbot

```bash
# Install certbot
sudo apt-get install certbot

# Get certificate
sudo certbot certonly --standalone -d yourdomain.com

# Certificates will be in:
# /etc/letsencrypt/live/yourdomain.com/
```

### Enable Nginx Proxy

```bash
# Start with nginx
docker compose --profile production up -d

# Update nginx.conf with SSL paths
# Then restart
docker compose restart nginx
```

---

## 🗄️ Database Backup

```bash
# Backup
docker compose exec db pg_dump -U postgres midas_db > backup_$(date +%Y%m%d).sql

# Restore
docker compose exec -T db psql -U postgres midas_db < backup_20231213.sql
```

---

## 📊 Monitoring

```bash
# View logs
docker compose logs -f api

# Check containers
docker compose ps

# Resource usage
docker stats
```

---

## 🐛 Troubleshooting

### API not starting

```bash
docker compose logs api
# Check for errors in environment variables
```

### Database connection failed

```bash
docker compose ps db
# Should show "Up (healthy)"

# Restart database
docker compose restart db
```

### Port already in use

```bash
# Change API_PORT in .env
nano .env  # Set API_PORT=8001
docker compose restart
```

### Missing limits table

```bash
# Recreate database with new schema
docker compose down
docker volume rm midas_postgres_data
docker compose up -d --build
```

---

## 🧹 Maintenance

### Stop Services

```bash
docker compose down
```

### Remove Everything (including data)

```bash
docker compose down -v
```

### View Container Logs

```bash
docker compose logs --tail=100 -f api
```

---

## ✅ Deployment Checklist

- [ ] Server prepared with Docker installed
- [ ] Repository cloned
- [ ] `.env` file created and configured
- [ ] `SECRET_KEY` generated
- [ ] `POSTGRES_PASSWORD` set
- [ ] `OPENAI_API_KEY` added
- [ ] `CORS_ORIGINS` configured
- [ ] `docker compose up -d --build` executed
- [ ] Health check passed
- [ ] First user registered
- [ ] HTTPS configured (production)
- [ ] Backups configured

---

**Support:** http://your-server:8000/docs
