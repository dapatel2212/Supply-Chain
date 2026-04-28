# 🚢 ShipTrack AI

A full-stack AI-powered shipment tracking platform with real-time vessel positioning, ML-based ETA prediction, route optimization, and automated email alerts.

---

## 📋 Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [API Reference](#api-reference)
- [ML Models](#ml-models)
- [External Integrations](#external-integrations)
- [Project Structure](#project-structure)

---

## ✨ Features

- **Live Shipment Tracking** — Real-time vessel position via ShipsGo v2 API (falls back to simulation for non-sea phases)
- **Interactive Map** — TomTom-powered map with route visualization and fallback map component
- **AI Analytics** — Google Gemini AI generates natural-language insights from shipment data
- **ML ETA Prediction** — Scikit-learn models trained from your own database to predict delivery times
- **Route Optimization** — Automated route suggestions using TomTom Routing API
- **Weather Integration** — OpenWeather data factored into delay calculations
- **Email Alerts** — Gmail SMTP notifications for shipment status changes and delays
- **Background Jobs** — Celery + Redis workers for async tracking updates and scheduled tasks
- **Dashboard Analytics** — On-time rates, delay stats, cargo distribution, and status breakdowns
- **JWT Authentication** — Secure login with 30-day access tokens

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 18, React Router 6, Recharts, Axios, Lucide React |
| **Backend** | Flask 2.3, SQLAlchemy 2.0, Flask-JWT-Extended |
| **Database** | PostgreSQL 15 (primary), TimescaleDB (supply chain data) |
| **Cache / Queue** | Redis 7, Celery 5 |
| **ML** | Scikit-learn, Pandas, NumPy |
| **AI** | Google Gemini 1.5 Flash / Pro |
| **Maps** | TomTom Maps & Routing API |
| **Tracking** | ShipsGo v2 API |
| **Weather** | OpenWeatherMap API |
| **Email** | Gmail SMTP |
| **Containers** | Docker + Docker Compose |

---

## 🏗 Architecture

```
┌─────────────────┐     ┌──────────────────────────────────────┐
│   React Frontend│────▶│  Flask Backend  (port 5000)          │
│   (port 3000)   │     │  ├── /api/shipments   (CRUD)         │
└─────────────────┘     │  ├── /api/analytics   (dashboard)    │
                        │  ├── /api/auth         (JWT)          │
                        │  └── /api/analytics/api-status       │
                        └───────────┬──────────────────────────┘
                                    │
              ┌─────────────────────┼──────────────────────┐
              ▼                     ▼                       ▼
        PostgreSQL              Redis 7             Celery Workers
        (shipments,          (task queue,          (tracking updates,
         ports, users)        caching)              scheduled beats)
```

---

## ✅ Prerequisites

- [Docker](https://www.docker.com/get-started) & Docker Compose
- A **TimescaleDB** instance running on host port `5433` with a `supply_chain` database (for ML training data)
- API keys for: TomTom, Google Gemini, OpenWeatherMap, ShipsGo
- A Gmail account with an [App Password](https://myaccount.google.com/apppasswords) enabled

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd shiptrack-ai-fixed
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Fill in all values in `.env` (see [Environment Variables](#environment-variables) below).

### 3. Build and start all services

```bash
docker-compose up --build
```

This will start:
- `postgres` on port `5432`
- `redis` on port `6379`
- `backend` (Flask + Gunicorn) on port `5000`
- `celery_worker` (async task processor)
- `celery_beat` (scheduled task runner)
- `frontend` (React dev server) on port `3000`

On first boot, the backend will automatically:
1. Create all database tables
2. Seed the database with demo data
3. Train the ML ETA prediction models

### 4. Open the app

```
http://localhost:3000
```

### Default login credentials (seeded)

| Email | Password |
|---|---|
| `admin@shiptrack.com` | `admin123` |

---

## ⚙️ Environment Variables

Copy `.env.example` to `.env` and set the following:

```env
# PostgreSQL (primary database)
DATABASE_URL=postgresql://admin:password123@localhost:5432/shipment_db

# TimescaleDB (supply chain ML data — host port 5433)
TIMESCALE_URL=postgresql://postgres:<password>@localhost:5433/supply_chain

# Redis
REDIS_URL=redis://localhost:6379/0

# Flask
FLASK_ENV=development
FLASK_APP=app.py
JWT_SECRET_KEY=your-super-secret-key-change-in-production

# TomTom (maps & routing)
TOMTOM_API_KEY=your_tomtom_api_key_here

# Google Gemini AI
GEMINI_API_KEY=your_gemini_api_key_here

# OpenWeatherMap
OPENWEATHER_API_KEY=your_openweather_api_key_here

# ShipsGo (vessel tracking)
SHIPSGO_API_KEY=your_shipsgo_api_key_here

# Gmail SMTP (spaces in app password are OK — code strips them)
GMAIL_SENDER=your_email@gmail.com
GMAIL_PASSWORD=xxxx xxxx xxxx xxxx

# Frontend
REACT_APP_API_URL=http://localhost:5000
REACT_APP_TOMTOM_KEY=your_tomtom_api_key_here
```

> **Gmail note:** Generate an App Password at https://myaccount.google.com/apppasswords. Paste it as-is (with or without spaces).

---

## 📡 API Reference

### Auth

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/login` | Login, returns JWT access token |

### Shipments

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/shipments` | List shipments (filter by `?status=`, `?limit=`) |
| `GET` | `/api/shipments/:id` | Get shipment details with port info |
| `POST` | `/api/shipments` | Register a new shipment |
| `PUT` | `/api/shipments/:id/track` | Trigger position update |

### Analytics

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/analytics/dashboard` | KPIs, status & cargo distributions (`?days=30`) |
| `GET` | `/api/analytics/ai-insights` | Gemini AI-generated insights |
| `GET` | `/api/analytics/api-status` | Health check for all external API connections |

### Health

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Backend liveness check |

---

## 🤖 ML Models

Models are trained automatically on startup from your PostgreSQL + TimescaleDB data.

| Model | Purpose | Algorithm |
|---|---|---|
| ETA Predictor | Predicts final delivery date | Random Forest / Gradient Boosting |
| Delay Classifier | Flags likely delays | Scikit-learn pipeline |

Model artifacts are saved to `backend/ml/saved_models/`. If training data is unavailable, the system falls back gracefully to rule-based estimates.

To retrain manually:

```bash
docker exec -it shiptrack_backend python -c "from ml.train_from_db import train_from_database; train_from_database()"
```

---

## 🔌 External Integrations

| Service | Purpose | Status |
|---|---|---|
| **ShipsGo v2** | Real vessel/container position at sea | Active (falls back to simulation) |
| **TomTom** | Interactive maps + route optimization | Active |
| **Google Gemini** | AI-generated analytics insights | Active (tries `gemini-1.5-flash` → `gemini-1.5-pro` → `gemini-pro`) |
| **OpenWeatherMap** | Weather data for delay estimation | Active |
| **Gmail SMTP** | Shipment status email notifications | Active (lazy-initialized on first send) |
| **Firebase** | Push notifications (configured via env) | Active |

Check live API status at: `GET /api/analytics/api-status`

---

## 📁 Project Structure

```
shiptrack-ai-fixed/
├── backend/
│   ├── app.py                    # Flask app factory, auth routes
│   ├── celery_app.py             # Celery configuration
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── database/
│   │   ├── db_setup.py           # SQLAlchemy models (User, Shipment, Port, ...)
│   │   └── seed_data.py          # Demo data seeder
│   ├── routes/
│   │   ├── shipment_routes.py    # Shipment CRUD endpoints
│   │   └── analytics_routes.py  # Dashboard + Gemini AI endpoints
│   ├── services/
│   │   ├── tracking_service.py   # Position update logic (ShipsGo + simulation)
│   │   ├── shipsgo_service.py    # ShipsGo v2 API client
│   │   ├── route_optimizer.py    # TomTom route optimization
│   │   ├── notification_service.py # Gmail SMTP alerts
│   │   └── weather_service.py    # OpenWeather client
│   ├── ml/
│   │   ├── eta_model.py          # ETA model definition
│   │   ├── train_from_db.py      # DB-driven model training
│   │   ├── generate_data.py      # Synthetic data generator
│   │   └── saved_models/         # Trained model artifacts
│   └── tasks/
│       └── tracking_tasks.py     # Celery async/scheduled tasks
├── frontend/
│   ├── src/
│   │   ├── App.js                # Router + layout
│   │   └── components/
│   │       ├── Map/              # TomTom map + fallback
│   │       ├── Shipments/        # List + register forms
│   │       └── Analytics/        # Dashboard charts + AI insights
│   ├── public/
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── .gitignore
```

---

## 🐛 Known Fixes Applied

This repository includes the following bug fixes over the original version:

- **Gemini AI** — Upgraded `google-generativeai` to `>=0.7.0`; added multi-model fallback chain
- **Gmail SMTP** — Strip spaces from app password; lazy SMTP init; added `EHLO` handshake fix
- **ShipsGo** — Migrated from deprecated v1 API to v2; integrated into tracking service

---

## 📄 License

MIT
