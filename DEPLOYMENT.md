# 🚀 Baraka AI Deployment Guide

**Complete deployment guide for setting up Baraka AI on a brand new server from scratch.**

---

## 📋 Table of Contents
- [Prerequisites](#-prerequisites)
- [Initial Server Setup](#-initial-server-setup)
- [Install Docker](#-install-docker)
- [Project Setup](#-project-setup)
- [Environment Configuration](#-environment-configuration)
- [Database Setup](#-database-setup)
- [Deploy with Docker Compose](#-deploy-with-docker-compose)
- [Nginx & SSL Setup](#-nginx--ssl-setup)
- [Post-Deployment](#-post-deployment)
- [Troubleshooting](#-troubleshooting)
- [Maintenance](#-maintenance)

---

## 🎯 Prerequisites

### Server Requirements
- **OS:** Ubuntu 22.04 LTS or Debian 12 (recommended)
- **CPU:** 4 cores (recommended), minimum 2 cores
- **RAM:** 8 GB (recommended), minimum 4 GB
- **Storage:** 80 GB SSD (NVMe preferred)
- **Network:** Public IP address, ports 80 and 443 open

### Required Accounts & Keys
- GitHub account (to clone repository)
- Domain name (for SSL certificates)
- **API Keys:**
  - OpenAI API key (`sk-proj-...`)
  - UzAI STT API key (for Uzbek speech-to-text)
  - Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- **Click.uz credentials** (for payments):
  - Service ID
  - Merchant ID
  - Secret Key

---

## 🔧 Initial Server Setup

### 1. Connect to Server
```bash
ssh root@YOUR_SERVER_IP
```

### 2. Create Non-Root User (Security Best Practice)
```bash
# Create user
adduser deploy
usermod -aG sudo deploy

# Switch to user
su - deploy
```

### 3. Update System
```bash
sudo apt update && sudo apt upgrade -y
```

### 4. Configure Firewall
```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
sudo ufw status
```

---

## 🐳 Install Docker

### Install Docker Engine
```bash
# Install dependencies
sudo apt install -y ca-certificates curl gnupg lsb-release

# Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Add user to docker group (avoid sudo)
sudo usermod -aG docker $USER

# Log out and back in for group changes to take effect
exit
su - deploy  # Or re-SSH
```

### Verify Installation
```bash
docker --version
docker compose version
```

---

## 📦 Project Setup

### 1. Clone Repository
```bash
cd ~
git clone https://github.com/komrxn/Midas_ai.git
cd Midas_ai
```

### 2. Create Directory Structure
```bash
# Data directories
mkdir -p bot/data
mkdir -p postgres_data

# Verify structure
ls -la
```

---

## ⚙️ Environment Configuration

### 1. Create Production Environment File
```bash
cp .env.example .env
nano .env
```

### 2. Configure Environment Variables

**`.env` file template:**
```bash
# ======================
# DATABASE
# ======================
POSTGRES_DB=midas_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=YOUR_STRONG_DB_PASSWORD_HERE  # Change this!

# ======================
# API SECURITY
# ======================
# Generate with: python3 -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=YOUR_32_CHAR_RANDOM_SECRET_HERE  # Change this!
ACCESS_TOKEN_EXPIRE_MINUTES=43200  # 30 days

# ======================
# AI SERVICES
# ======================
OPENAI_API_KEY=sk-proj-YOUR_OPENAI_KEY_HERE
UZAI_API_KEY=YOUR_UZAI_KEY_HERE
UZAI_STT_URL=https://api.uzai.uz/v1/stt  # Or your STT endpoint

# ======================
# TELEGRAM BOT
# ======================
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_FROM_BOTFATHER

# ======================
# PAYMENT (Click.uz)
# ======================
CLICK_SERVICE_ID=YOUR_SERVICE_ID
CLICK_MERCHANT_ID=YOUR_MERCHANT_ID
CLICK_SECRET_KEY=YOUR_CLICK_SECRET_KEY

# ======================
# FRONTEND
# ======================
VITE_API_URL=https://yourdomain.com/midas-api
```

### 3. Secure Environment File
```bash
chmod 600 .env
```

---

## 🗄️ Database Setup

### 1. Initialize Database
```bash
# Start only the database first
docker compose up -d db

# Wait for database to be ready
docker compose logs -f db
# Look for: "database system is ready to accept connections"
# Press Ctrl+C to exit logs
```

### 2. Run Migrations
```bash
docker compose exec db psql -U postgres -d midas_db -f /docker-entrypoint-initdb.d/01-schema.sql
```

### 3. Seed Default Categories (Optional but Recommended)
```bash
# This creates default expense/income categories
docker compose exec api python -c "
from api.database import get_db
from api.scripts.seed_default_categories import seed_default_categories
import asyncio

async def main():
    async for db in get_db():
        await seed_default_categories(db)
        break

asyncio.run(main())
"
```

---

## 🚀 Deploy with Docker Compose

### 1. Build and Start All Services
```bash
docker compose up -d --build
```

**This starts:**
- `db` — PostgreSQL database
- `api` — FastAPI backend
- `bot` — Telegram bot
- `frontend` — Vue.js web app

### 2. Verify Deployment
```bash
# Check container status
docker compose ps

# Expected output:
# NAME              STATUS         PORTS
# midas_postgres    Up (healthy)   5432/tcp
# midas_api         Up (healthy)   8000/tcp
# midas_bot         Up             -
# midas_frontend    Up             80/tcp

# Check logs
docker compose logs -f api
docker compose logs -f bot

# Test API health
curl http://localhost:8001/health
# Should return: {"status":"ok"}
```

---

## 🔒 Nginx & SSL Setup

### 1. Install Nginx
```bash
sudo apt install -y nginx
```

### 2. Configure Nginx
Create `/etc/nginx/sites-available/midas`:

```nginx
# Redirect HTTP to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Let's Encrypt verification
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    location / {
        return 301 https://$host$request_uri;
    }
}

# HTTPS Server Block
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Certificates (will be added by certbot)
    ssl_certificate /etc/letsencrypt/live/baraka-ai.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/baraka-ai.com/privkey.pem;
    
    # SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;

    # Frontend (Root)
    location / {
        proxy_pass http://localhost:3001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API Backend
    location /midas-api/ {
        proxy_pass http://localhost:8001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Increase timeouts for AI requests
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

### 3. Enable Site
```bash
sudo ln -s /etc/nginx/sites-available/midas /etc/nginx/sites-enabled/
sudo nginx -t  # Test configuration
```

### 4. Install SSL Certificate (Let's Encrypt)
```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal is configured automatically
# Verify: sudo certbot renew --dry-run
```

### 5. Restart Nginx
```bash
sudo systemctl restart nginx
sudo systemctl enable nginx
```

---

## ✅ Post-Deployment

### 1. Health Checks
```bash
# API Health
curl https://yourdomain.com/midas-api/health

# API Docs
open https://yourdomain.com/midas-api/docs

# Frontend
open https://yourdomain.com
```

### 2. Test Telegram Bot
1. Open Telegram and find your bot (@YourBotName)
2. Send `/start`
3. Register with phone number
4. Test voice/photo messages

### 3. Set Up Monitoring (Optional but Recommended)
```bash
# Install monitoring tools
sudo apt install -y htop iotop nethogs

# Monitor logs in real-time
docker compose logs -f --tail=50

# Set up log rotation (prevent disk fill)
sudo nano /etc/docker/daemon.json
```

Add:
```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

Restart Docker:
```bash
sudo systemctl restart docker
docker compose up -d  # Restart containers
```

---

## 🔧 Troubleshooting

### Container Won't Start
```bash
# Check logs
docker compose logs api
docker compose logs bot

# Check container status
docker compose ps

# Restart specific service
docker compose restart api
```

### Database Connection Issues
```bash
# Check database is healthy
docker compose exec db pg_isready -U postgres

# Connect to database
docker compose exec db psql -U postgres -d midas_db

# Verify tables exist
\dt
```

### API Returns 500 Errors
```bash
# Check environment variables
docker compose exec api env | grep -E 'OPENAI|DATABASE|SECRET'

# Check database migrations
docker compose exec db psql -U postgres -d midas_db -c "\d users"
```

### Nginx Issues
```bash
# Test configuration
sudo nginx -t

# Check logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# Restart nginx
sudo systemctl restart nginx
```

### SSL Certificate Issues
```bash
# Renew manually
sudo certbot renew --force-renewal

# Check certificate status
sudo certbot certificates
```

---

## 🛠️ Maintenance

### Updates
```bash
# Pull latest changes
cd ~/Midas_ai
git pull

# Rebuild and restart
docker compose up -d --build

# Prune old images (save space)
docker system prune -a
```

### Backups

#### Database Backup
```bash
# Create backup
docker compose exec db pg_dump -U postgres midas_db > backup_$(date +%Y%m%d).sql

# Restore backup
docker compose exec -T db psql -U postgres -d midas_db < backup_20260114.sql
```

#### Full Backup Script
Create `~/backup.sh`:
```bash
#!/bin/bash
BACKUP_DIR=~/backups
mkdir -p $BACKUP_DIR
DATE=$(date +%Y%m%d_%H%M%S)

# Database
docker compose exec -T db pg_dump -U postgres midas_db > $BACKUP_DIR/db_$DATE.sql

# Environment
cp .env $BACKUP_DIR/env_$DATE.bak

# Bot data
tar -czf $BACKUP_DIR/bot_data_$DATE.tar.gz bot/data/

echo "Backup completed: $BACKUP_DIR/*_$DATE.*"
```

Make executable and run:
```bash
chmod +x ~/backup.sh
./backup.sh

# Schedule daily backups (cron)
crontab -e
# Add: 0 2 * * * /home/deploy/backup.sh
```

### Monitoring Disk Space
```bash
# Check disk usage
df -h

# Check Docker usage
docker system df

# Clean up if needed
docker system prune -a --volumes  # WARNING: Removes all unused data
```

### Scaling (If Needed)

#### Horizontal Scaling
```bash
# Scale API instances
docker compose up -d --scale api=3
```

#### Vertical Scaling
Update `docker-compose.yml`:
```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
```

---

## 📞 Support

- **Documentation:** [README.md](README.md), [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- **Admin Commands:** [ADMIN_COMMANDS.md](ADMIN_COMMANDS.md)
- **Issues:** [GitHub Issues](https://github.com/komrxn/Midas_ai/issues)

---

**🎉 Deployment Complete! Your Baraka AI platform is now live.**
