# 🌿 Greenmind AI - Django Ninja + Vue 3

Moderna full-stack aplikacija z Django Ninja (async) backend-om in Vue 3 frontend-om.

## ✨ Funkcionalnosti

- 🔐 **Async Authentication** - Django Ninja z JWT tokeni
- 🎨 **Čudovit UI** - Vue 3 + TypeScript + Naive UI (dark theme)
- 📧 **OAuth2** - Google in Apple prijava
- ⚡ **Celery** - Async task processing
- 🐳 **Docker** - Celoten stack v Docker containers
- �� **Flower** - Celery monitoring
- 📦 **Redis** - Caching in message broker
- 🐘 **PostgreSQL** - Production-ready database

## 🛠️ Tech Stack

### Backend
- Django 5.0
- Django Ninja 1.1 (FastAPI-style async API)
- Celery 5.3 + Redis
- PostgreSQL
- JWT Authentication
- django-allauth (OAuth2)

### Frontend
- Vue 3 + TypeScript
- Naive UI (najlepši UI framework)
- Pinia (state management)
- Vue Router
- Axios
- Vite

## 🚀 Zagon

### Z Docker Compose (priporočeno)

```bash
# Zaženi vse servise
docker-compose up --build

# Aplikacija bo dostopna na:
# Frontend: http://localhost:5173
# Backend API: http://localhost:8090/api
# API Docs: http://localhost:8090/api/docs
# Flower (Celery): http://localhost:5555
# PostgreSQL: localhost:5442
```

### Lokalno (brez Docker-ja)

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Zaženi PostgreSQL na portu 5442
# Zaženi Redis

python manage.py migrate
python manage.py create_test_user
python manage.py runserver 0.0.0.0:8090

# V drugem terminalu - Celery worker
celery -A config worker -l info

# V tretjem terminalu - Celery beat
celery -A config beat -l info

# Flower (opcijsko)
celery -A config flower
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

## 👤 Test Account

```
Email: mihael@example.com
Username: mihaelv
Password: corelite
```

## 📝 API Endpoints

- `POST /api/auth/register` - Registracija
- `POST /api/auth/login` - Prijava
- `GET /api/auth/me` - Trenutni uporabnik (zahteva JWT)
- `POST /api/auth/logout` - Odjava
- `GET /api/auth/google/login` - Google OAuth2
- `GET /api/auth/apple/login` - Apple OAuth2

## 🎨 UI Features

- Glassmorphism design
- Dark theme
- Gradient backgrounds
- Smooth animations
- Responsive layout
- OAuth2 buttons (Google, Apple)

## 🔧 Konfigurac ija

### Backend (.env)

```env
DB_NAME=authdb
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5442

REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0

GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-secret

APPLE_CLIENT_ID=your-apple-client-id
```

### Frontend (.env)

```env
VITE_API_URL=http://localhost:8090/api
```

## 📦 Docker Services

- **db** - PostgreSQL 16 (port 5442)
- **redis** - Redis 7 (port 6379)
- **backend** - Django Ninja API (port 8090)
- **celery_worker** - Async task worker
- **celery_beat** - Periodic tasks
- **flower** - Celery monitoring (port 5555)
- **frontend** - Vue 3 app (port 5173)

## 🎯 Naslednji koraki

1. Nastavi OAuth2 credentials za Google/Apple
2. Konfiguriraj email backend za pošiljanje emailov
3. Dodaj production settings
4. Nastavi HTTPS
5. Dodaj rate limiting
6. Implementiraj dodatne funkcionalnosti

## 📄 Licenca

MIT
