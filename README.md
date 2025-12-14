# 🤖 Midas AI Accountant API

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-blue.svg)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-green.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)

**Production-ready RESTful API for AI-powered expense & income tracking**

[Features](#-features) • [Quick Start](#-quick-start) • [API Docs](#-api-endpoints) • [Deployment](DEPLOYMENT.md)

</div>

---

## ✨ Features

### Core Functionality
- 💰 **Transactions** — Income & expense tracking with full CRUD
- 🏷️ **Categories** — Default + custom categories with protection
- 📊 **Analytics** — Balance, breakdowns, trends, dashboard
- 💸 **Debts** — Track borrowed/lent money with statuses
- 📈 **Limits** — Budget limits with auto-spending calculation

### AI-Powered
- 🤖 **Smart Parsing** — Text, voice, and image transaction parsing
- 🧠 **Auto-Categorization** — AI category suggestions with confidence
- 🗣️ **Voice Support** — Whisper-based voice message parsing
- 📸 **Receipt OCR** — GPT-4 Vision for receipt/check parsing

### Technical
- 🔐 **JWT Auth** — Secure authentication with bcrypt
- 🌍 **Multi-User** — Full isolation between users
- 💱 **Multi-Currency** — UZS, USD, EUR, RUB support
- 🚀 **Async** — High-performance async PostgreSQL
- 🐳 **Docker Ready** — One-command deployment

---

## 🎯 API Endpoints (33 total)

### 🔐 Authentication (3)
- `POST /auth/register` — Register user
- `POST /auth/login` — Get JWT token
- `GET /auth/me` — Current user

### 💰 Transactions (5)
- `POST /transactions` — Create
- `GET /transactions` — List (filters: type, category, date range, pagination)
- `GET /transactions/{id}` — Get one
- `PUT /transactions/{id}` — Update
- `DELETE /transactions/{id}` — Delete

### 🏷️ Categories (4)
- `GET /categories` — List all
- `POST /categories` — Create custom
- `PUT /categories/{id}` — Update
- `DELETE /categories/{id}` — Delete (default protected)

### 📊 Analytics (4)
- `GET /analytics/balance` — Income/expense totals
- `GET /analytics/category-breakdown` — Spending by category
- `GET /analytics/trends` — Time-series data
- `GET /analytics/summary` — Dashboard data

### 💸 Debts (7)
- `POST /debts` — Create debt
- `GET /debts` — List (filters: type, status)
- `GET /debts/balance` — Balance summary
- `GET /debts/{id}` — Get one
- `PUT /debts/{id}` — Update
- `POST /debts/{id}/mark-paid` — Mark as settled
- `DELETE /debts/{id}` — Delete

### 📈 Limits (6)
- `POST /limits` — Create budget limit
- `GET /limits` — List with auto spending calc
- `GET /limits/current` — Current month summary
- `GET /limits/{id}` — Get one
- `PUT /limits/{id}` — Update
- `DELETE /limits/{id}` — Delete

### 🤖 AI Parsing (4)
- `POST /ai/parse-transaction?input_type=text` — Parse text
- `POST /ai/parse-transaction?input_type=voice` — Parse voice
- `POST /ai/parse-transaction?input_type=image` — Parse receipt
- `POST /ai/suggest-category` — Suggest category

---

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone
git clone https://github.com/yourusername/midas.git
cd midas

# Configure
cp env.production.example .env
nano .env  # Set SECRET_KEY, POSTGRES_PASSWORD, OPENAI_API_KEY

# Deploy
docker compose up -d --build

# Verify
curl http://localhost:8000/health
```

**API:** http://localhost:8000  
**Docs:** http://localhost:8000/docs

### Option 2: Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Setup database
createdb midas_db
psql -U postgres -d midas_db -f schema.sql

# Configure .env
cp .env.example .env
# Set DATABASE_URL, SECRET_KEY, OPENAI_API_KEY

# Run
uvicorn api.main:app --reload
```

---

## 📖 Usage Examples

### 1. Register & Login

```bash
# Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","email":"admin@test.com","password":"admin123"}'

# Login
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.access_token')
```

### 2. Create Transaction

```bash
curl -X POST http://localhost:8000/transactions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "expense",
    "amount": 50000,
    "description": "Taxi",
    "transaction_date": "2025-12-13T10:00:00Z"
  }'
```

### 3. AI Parse Text

```bash
curl -X POST "http://localhost:8000/ai/parse-transaction?input_type=text" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text":"купил кофе за 25000 сум"}'
```

### 4. Get Analytics

```bash
# Balance
curl "http://localhost:8000/analytics/balance?start_date=2025-12-01" \
  -H "Authorization: Bearer $TOKEN"

# Category breakdown
curl "http://localhost:8000/analytics/category-breakdown" \
  -H "Authorization: Bearer $TOKEN"
```

### 5. Create Debt

```bash
curl -X POST http://localhost:8000/debts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "i_owe",
    "person_name": "John",
    "amount": 100000,
    "description": "Borrowed for rent",
    "due_date": "2025-12-31"
  }'
```

### 6. Create Budget Limit

```bash
# Get category ID first
CATEGORY=$(curl -s http://localhost:8000/categories \
  -H "Authorization: Bearer $TOKEN" | jq -r '.[0].id')

# Create limit
curl -X POST http://localhost:8000/limits \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"category_id\": \"$CATEGORY\",
    \"amount\": 500000,
    \"period_start\": \"2025-12-01\",
    \"period_end\": \"2025-12-31\"
  }"
```

---

## 🏗️ Architecture

```
api/
├── models/          # SQLAlchemy ORM models
│   ├── user.py
│   ├── category.py
│   ├── transaction.py
│   ├── debt.py
│   └── limit.py
├── schemas/         # Pydantic request/response schemas
│   ├── auth.py
│   ├── transaction.py
│   ├── category.py
│   ├── analytics.py
│   ├── debt.py
│   ├── limit.py
│   └── ai.py
├── routers/         # API endpoint handlers
│   ├── auth.py
│   ├── transactions.py
│   ├── categories.py
│   ├── analytics.py
│   ├── debts.py
│   ├── limits.py
│   └── ai.py
├── services/        # Business logic
│   └── ai_parser.py
├── auth/            # JWT authentication
│   └── jwt.py
├── config.py        # Environment settings
├── database.py      # SQLAlchemy setup
└── main.py          # FastAPI app
```

**Database Tables:**
- `users` — User accounts with JWT auth
- `categories` — Default + custom categories
- `transactions` — Income & expense records
- `debts` — Borrowed/lent money tracking
- `limits` — Budget limits per category

---

## 🔧 Configuration

### Required Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/midas_db

# JWT Auth (generate with: python -c "import secrets; print(secrets.token_urlsafe(32))")
SECRET_KEY=your-32-char-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=43200  # 30 days

# OpenAI
OPENAI_API_KEY=sk-proj-your-key-here

# CORS (frontend URLs)
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

### Default Categories

**Expenses:**
🍔 Питание, 🚕 Транспорт, 🎮 Развлечения, 🛍️ Покупки, 💇 Услуги, 💊 Здоровье, 📚 Образование, 🏠 Жильё, 💳 Счета

**Income:**
💰 Зарплата, 💼 Подработка, ↩️ Возврат

---

## 📚 Documentation

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json
- **Frontend API Docs:** [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- **Deployment Guide:** [DEPLOYMENT.md](DEPLOYMENT.md)
- **Testing Guide:** [TESTING.md](TESTING.md)

---

## 🧪 Testing

### Unit Tests

```bash
# Run all tests
python scripts/run_tests.py

# Skip AI tests (no OpenAI key needed)
python scripts/run_tests.py --skip-ai

# Verbose output
python scripts/run_tests.py -v
```

**Test Coverage:**
- ✅ 25+ unit tests
- ✅ Auth (register, login, JWT)
- ✅ Transactions (CRUD, filters)
- ✅ Categories (CRUD, default protection)
- ✅ Analytics (balance, breakdown, trends)
- ✅ AI parsing (optional)

### Manual Testing

```bash
# Interactive Swagger UI
open http://localhost:8000/docs

# Test script
chmod +x scripts/test_api.sh
./scripts/test_api.sh
```

---

## 🚢 Production Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete guide.

**Quick Deploy:**
```bash
# SSH to server
ssh user@server.com

# Clone & configure
git clone https://github.com/yourusername/midas.git
cd midas
cp env.production.example .env
nano .env  # Set secrets

# Deploy
docker compose up -d --build

# Verify
curl http://localhost:8000/health
```

---

## 🆕 What's New in v2.0.0

### New Features
- ✨ **Debts Management** — Track borrowed/lent money
- ✨ **Budget Limits** — Set spending limits with auto tracking
- 🔄 **Auto Spending Calc** — Limits auto-calculate spent from transactions
- 📊 **Enhanced Analytics** — New summary endpoints

### Technical Improvements
- 🐳 **Docker-ready** — One-command deployment
- 🗄️ **Schema Updates** — Added limits table, triggers, indexes
- 🔐 **Security** — bcrypt direct integration, improved JWT
- 📝 **Documentation** — Complete API docs for frontend

### Migration from v1.x
```bash
# Database schema changed - backup first!
docker compose exec db pg_dump -U postgres midas_db > backup.sql

# Then recreate with new schema
docker compose down
docker volume rm midas_postgres_data
docker compose up -d --build
```

---

## 💡 Use Cases

- 📱 **Mobile/Web Apps** — Backend for expense tracker apps
- 🤖 **Telegram Bots** — AI-powered finance bot backends
- 📊 **Financial Dashboards** — Analytics API for dashboards
- 🏦 **Personal Finance Tools** — Budget & debt management
- 🧾 **Receipt Processing** — OCR & auto-categorization

---

## 📄 License

MIT License

---

<div align="center">

**Made with ❤️ for smart finance tracking**

[Documentation](API_DOCUMENTATION.md) • [Deploy](DEPLOYMENT.md) • [Test](TESTING.md)

⭐ Star this repo if you find it useful!

</div>
