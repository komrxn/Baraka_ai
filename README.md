# 🤖 Baraka AI — AI-Powered Finance Assistant

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-success.svg)
![Vue.js](https://img.shields.io/badge/Vue.js-3.4-green.svg)
![Telegram](https://img.shields.io/badge/Telegram-Bot-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)

**Production-ready AI-powered personal finance platform with Telegram bot, web app, and subscription system**

[Features](#-features) • [Quick Start](#-quick-start) • [Deployment](DEPLOYMENT.md) • [API Docs](API_DOCUMENTATION.md)

</div>

---

## ✨ Features

### 💎 Subscription & Monetization
- 💳 **Freemium Model** — Free tier with usage limits (20 voice, 10 photo messages)
- 🎁 **3-Day Free Trial** — Test premium features risk-free
- 💰 **Click.uz & Payme Integration** — Automated subscription payments for Uzbekistan
- 👑 **Premium Features** — Unlimited usage, advanced analytics, budget limits, debt tracking

### 🤖 AI-Powered Intelligence
- 🧠 **Smart Transaction Parsing** — Text, voice (Whisper), and image (GPT-4 Vision) parsing
- 🗣️ **Voice Messages** — Speak transactions in Uzbek, Russian, or English
- 📸 **Receipt OCR** — Automatically extract amounts and items from receipts/checks
- 🏷️ **Auto-Categorization** — AI suggests categories with confidence scores
- 💱 **Multi-Currency Support** — Record transactions in USD, EUR, RUB + auto-convert to UZS (Pro/Premium)

### 💱 Currency Features (NEW!)
- 📊 **Live Exchange Rates** — Real-time rates from Central Bank of Uzbekistan
- 🔄 **Auto-Conversion** — Foreign currency transactions auto-convert to UZS
- 🌍 **70+ Currencies** — USD, EUR, RUB, GBP, CNY, KZT, AED, TRY and more
- 📈 **Daily Changes** — Track currency rate movements

### 📊 Financial Management
- 💰 **Transactions** — Track income and expenses with full CRUD
- 🏷️ **Categories** — 27 default + unlimited custom categories
- 📈 **Budget Limits** — Set spending limits with auto-calculation
- 💸 **Debt Tracking** — Manage borrowed/lent money with reminders
- 📊 **Analytics** — Balance trends, category breakdowns, spending insights

### 🌐 Multi-Platform
- 📱 **Telegram Bot** — Native bot interface with keyboards and inline buttons
- 💻 **Web App** — Vue.js Progressive Web App (PWA) with Telegram Mini Apps
- 🌍 **Multi-Language** — Uzbek, Russian, English support

### 🔒 Technical Excellence
- 🔐 **Telegram-Native Auth** — Phone number + JWT authentication
- 🚀 **Async Architecture** — High-performance async PostgreSQL with SQLAlchemy
- 🐳 **Docker-Ready** — One-command deployment with Docker Compose
- 📡 **RESTful API** — 40+ endpoints with OpenAPI documentation
- 🔄 **Payment Webhooks** — Real-time Click.uz/Payme payment processing


---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│                     USER                         │
└───────────┬──────────────────┬──────────────────┘
            │                  │
    ┌───────▼────────┐  ┌──────▼─────────┐
    │  Telegram Bot  │  │  Vue.js Web App │
    │   (Python)     │  │   (TypeScript)  │
    └───────┬────────┘  └──────┬──────────┘
            │                  │
            └──────┬───────────┘
                   │
            ┌──────▼──────┐
            │  FastAPI    │
            │  Backend    │
            └──────┬──────┘
                   │
        ┌──────────┼──────────┐
        │          │          │
   ┌────▼────┐ ┌──▼───┐ ┌────▼────┐
   │PostgreSQL│ │OpenAI│ │Click.uz │
   │   DB    │ │  API │ │Payments │
   └─────────┘ └──────┘ └─────────┘
```

### Tech Stack

**Backend:**
- FastAPI (Python 3.11+)
- SQLAlchemy 2.0 (async)
- PostgreSQL 15+
- OpenAI API (GPT-4, Whisper)
- UzAI STT (Uzbek speech recognition)

**Frontend:**
- Vue.js 3.4
- PrimeVue components
- Pinia state management
- Vite build tool

**Bot:**
- python-telegram-bot
- Async handlers
- Inline keyboards

**Infrastructure:**
- Docker & Docker Compose
- Nginx (reverse proxy)
- Let's Encrypt SSL
- Alembic migrations

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- OpenAI API key
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))

### 1. Clone Repository
```bash
git clone https://github.com/komrxn/Midas_ai.git
cd Midas_ai
```

### 2. Configure Environment
```bash
cp .env.example .env
nano .env
```

**Required variables:**
```bash
# Database
POSTGRES_PASSWORD=your_secure_password

# JWT Secret (generate: python3 -c "import secrets; print(secrets.token_urlsafe(32))")
SECRET_KEY=your_random_32_char_secret

# API Keys
OPENAI_API_KEY=sk-proj-your-key
TELEGRAM_BOT_TOKEN=your:bot_token

# Click.uz (for payments)
CLICK_SERVICE_ID=your_service_id
CLICK_MERCHANT_ID=your_merchant_id
CLICK_SECRET_KEY=your_secret

# Frontend URL
VITE_API_URL=http://localhost:8001
```

### 3. Deploy
```bash
docker compose up -d --build
```

### 4. Verify
```bash
# Check services
docker compose ps

# Test API
curl http://localhost:8001/health
# => {"status":"ok"}

# Open Swagger docs
open http://localhost:8001/docs

# Open Web App
open http://localhost:3001
```

---

## 📱 Telegram Bot Usage

### Registration
1. Find your bot on Telegram (@YourBotName)
2. Send `/start`
3. Select language (🇷🇺 Русский / 🇺🇿 O'zbekcha / 🇬🇧 English)
4. Enter your name
5. Share phone number (security verified)

### Core Commands
- `/start` — Register or login
- `/profile` — View subscription status and usage
- `/help` — Show command list
- `/language` — Change language

### Transaction Input Methods

**1. Text Messages:**
```
купил кофе за 25000
потратил 50000 на такси
получил зарплату 5000000
```

**2. Voice Messages:**
- Record voice message in any language
- Bot transcribes and parses automatically

**3. Photo Messages:**
- Send receipt/check photo
- AI extracts amount and items

**4. Main Keyboard:**
- 📊 Баланс — View balance
- 📝 Транзакции — Transaction history
- 📈 Лимиты — Budget limits
- 💸 Долги — Debts
- 📊 Аналитика — Analytics
- 👤 Профиль — Profile
- 🌟 Premium — Upgrade to premium

---

## 💎 Subscription Plans

### Free Tier
- ✅ Unlimited text message transactions
- ✅ 20 voice message parses
- ✅ 10 photo/receipt parses
- ✅ Basic analytics
- ⏱️ Usage resets on new registration

### Premium (79,000 UZS/month)
- ✅ **Unlimited** voice messages
- ✅ **Unlimited** photo/receipt parsing
- ✅ Advanced analytics and insights
- ✅ Budget limits with notifications
- ✅ Debt tracking with reminders
- ✅ Priority support

### Free Trial
- 🎁 3 days of full premium access
- ⚡ No credit card required
- 🔄 One-time offer

---

## 📖 API Endpoints

### 🔐 Authentication (4)
- `POST /auth/register` — Register via Telegram
- `POST /auth/login` — Login with phone
- `POST /auth/telegram-auth` — Telegram Mini Apps auth
- `GET /auth/me` — Current user info
- `POST /auth/usage` — Increment usage counters

### 💰 Transactions (5)
- `POST /transactions` — Create
- `GET /transactions` — List with filters
- `GET /transactions/{id}` — Get one
- `PUT /transactions/{id}` — Update
- `DELETE /transactions/{id}` — Delete

### 🏷️ Categories (4)
- `GET /categories` — List all
- `POST /categories` — Create custom
- `PUT /categories/{id}` — Update
- `DELETE /categories/{id}` — Delete

### 📊 Analytics (4)
- `GET /analytics/balance` — Income/expense totals
- `GET /analytics/category-breakdown` — Spending by category
- `GET /analytics/trends` — Time-series data
- `GET /analytics/summary` — Dashboard

### 💸 Debts (7)
- `POST /debts` — Create
- `GET /debts` — List with filters
- `GET /debts/balance` — Summary
- `GET /debts/{id}` — Get one
- `PUT /debts/{id}` — Update
- `POST /debts/{id}/mark-paid` — Mark paid
- `DELETE /debts/{id}` — Delete

### 📈 Limits (6)
- `POST /limits` — Create budget limit
- `GET /limits` — List
- `GET /limits/current` — Current month
- `GET /limits/{id}` — Get one
- `PUT /limits/{id}` — Update
- `DELETE /limits/{id}` — Delete

### 🤖 AI Parsing (3)
- `POST /ai/parse-transaction?input_type=text`
- `POST /ai/parse-transaction?input_type=voice`
- `POST /ai/parse-transaction?input_type=image`

### 💳 Subscriptions (4)
- `GET /subscriptions/status` — Current subscription
- `POST /subscriptions/trial` — Activate trial
- `POST /subscriptions/prepare-payment` — Generate Click.uz payment URL
- `POST /subscriptions/click-webhook` — Payment callback

**Full API documentation:** [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

---

## 📁 Project Structure

```
.
├── api/                    # FastAPI Backend
│   ├── models/             # SQLAlchemy ORM models
│   │   ├── user.py         # User + subscription fields
│   │   ├── category.py
│   │   ├── transaction.py
│   │   ├── debt.py
│   │   ├── limit.py
│   │   └── click_transaction.py
│   ├── routers/            # API endpoints
│   │   ├── auth.py
│   │   ├── transactions.py
│   │   ├── categories.py
│   │   ├── analytics.py
│   │   ├── debts.py
│   │   ├── limits.py
│   │   ├── ai.py
│   │   └── subscriptions.py
│   ├── services/           # Business logic
│   │   ├── ai_parser.py
│   │   ├── click.py        # Click.uz integration
│   │   └── notification.py  # Telegram notifications
│   ├── auth/               # JWT authentication
│   └── main.py
│
├── bot/                    # Telegram Bot
│   ├── handlers/           # Message handlers
│   │   ├── commands.py
│   │   ├── messages.py
│   │   ├── voice.py
│   │   ├── photo.py
│   │   └── subscriptions.py
│   ├── locales/            # i18n (uz/ru/en)
│   ├── api_client.py       # Backend API client
│   └── main.py
│
├── finance-tracker/        # Vue.js Frontend
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── store/          # Pinia stores
│   │   ├── composables/
│   │   └── router/
│   └── Dockerfile
│
├── alembic/                # Database migrations
├── docker-compose.yml
├── DEPLOYMENT.md           # Production deployment guide
├── API_DOCUMENTATION.md
├── ADMIN_COMMANDS.md
└── README.md
```

---

## 🚢 Production Deployment

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for complete guide:
- Server setup (Ubuntu/Debian)
- Docker installation
- SSL certificates (Let's Encrypt)
- Nginx configuration
- Database setup
- Monitoring & backups

**Quick deploy:**
```bash
# On server
git clone https://github.com/komrxn/Midas_ai.git
cd Midas_ai
cp .env.example .env
nano .env  # Configure secrets
docker compose up -d --build
```

---

## 🔧 Development

### Run Locally (without Docker)

```bash
# Install dependencies
pip install -r requirements.txt
cd finance-tracker && npm install

# Setup database
createdb midas_db
alembic upgrade head

# Run backend
uvicorn api.main:app --reload

# Run frontend (separate terminal)
cd finance-tracker
npm run dev

# Run bot (separate terminal)
python -m bot.main
```

### Run Tests
```bash
# Backend tests
pytest

# Frontend tests
cd finance-tracker
npm run test
```

---

## 🌍 Localization

Supported languages:
- 🇺🇿 **O'zbekcha** (Uzbek)
- 🇷🇺 **Русский** (Russian)
- 🇬🇧 **English**

Translation files: `bot/locales/{uz,ru,en}/`

---

## 📄 License

MIT License — see [LICENSE](LICENSE) file.

---

## 🤝 Contributing

Contributions welcome! Please read contributing guidelines and submit PRs.

---

<div align="center">

**Made with ❤️ in Uzbekistan**

[Deployment Guide](DEPLOYMENT.md) • [API Docs](API_DOCUMENTATION.md) • [Admin Commands](ADMIN_COMMANDS.md)

⭐ **Star this repo if you find it useful!**

</div>
