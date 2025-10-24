
# FindSouth — Monorepo (FastAPI backend + Nuxt 3 frontend)

A full‑stack web application for managing and visualizing missing‑persons submissions in South Africa.

- Backend: FastAPI + SQLAlchemy + Alembic + Auth0 JWT auth + in‑process TTL caching. Static files are served under `/files`.
- Frontend: Nuxt 3 (SPA/static) with Tailwind UI, Pinia, and Google Maps integration for an admin heat‑map dashboard.
- Age progression: Integrates with public Hugging Face Spaces via `gradio_client` to generate age‑progressed images and caches results locally.

## Table of Contents
- [Repository layout](#repository-layout)
- [Tech stack](#tech-stack)
- [Quick start](#quick-start)
  - [Backend](#backend)
  - [Frontend](#frontend)
- [Key backend capabilities](#key-backend-capabilities)
- [Primary API endpoints](#primary-api-endpoints)
- [Age progression service](#age-progression-service)
- [Frontend features](#frontend-features)
- [Environment variables](#environment-variables)
  - [Backend (.env)](#backend-env)
  - [Frontend (.env)](#frontend-env)
- [Development workflow tips](#development-workflow-tips)
- [Building for production](#building-for-production)
- [Troubleshooting](#troubleshooting)
- [More details](#more-details)
- [Acceptance](#acceptance)

## Repository layout
- api/ — FastAPI backend (documentation in [api/README.md](api/README.md))
- frontend/ — Nuxt 3 frontend (README in [frontend/README.md](frontend/README.md))

## Tech stack
- Python 3.11+, FastAPI, Pydantic, SQLAlchemy (async), Alembic, JWT (HS256), Uvicorn, Loguru
- PostgreSQL (development and production)
- Nuxt 3, Vue 3, Pinia, @nuxt/ui, Tailwind, Google Maps JS API
- Hugging Face Spaces via `gradio_client` for age progression

## Quick start
Run the backend and frontend in two terminals.

### Backend
```bash
cd api
# Create virtualenv and install
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Copy env and configure DB + Auth0 values
cp .env.example .env

# (Optional) Create dev database
chmod +x scripts/create_db.sh
DB_NAME=find_south DB_USER=postgres DB_PASSWORD=postgres ./scripts/create_db.sh

# Run migrations
alembic upgrade head

# Start API (dev, auto‑reload)
uvicorn app.main:app --reload
# API: http://localhost:8000 | Docs: http://localhost:8000/docs | OpenAPI: /swagger.json | Health: /health
```

### Frontend
```bash
cd frontend
# Install dependencies
npm install

# Configure .env (see values below)
# NUXT_BASE_API_URL=http://localhost:8000
# NUXT_HOME_URL=/
# NUXT_PUBLIC_SITE_URL=http://localhost:3000
# NUXT_GOOGLE_MAPS_API_KEY=your_google_maps_key
# (optional) NUXT_GOOGLE_MAPS_MAP_ID=your_custom_map_id

# Dev server
npm run dev
# App: http://localhost:3000
```

## Key backend capabilities
- Submissions CRUD with image uploads (stored under `files/submissions` and served via `/files/submissions/...`).
- Public list and detail of published/closed submissions.
- User‑scoped list (`/submissions/mine`) and admin summary (`/submissions/summary`) with TTL caching.
- Age progression endpoint that generates or returns a cached image for a submission’s first image.

## Primary API endpoints
Base URL: http://localhost:8000

Submissions controller: [api/app/api/controllers/submissions_controller.py](api/app/api/controllers/submissions_controller.py)

- GET `/health` — liveness
- GET `/me` — current user (requires valid JWT)
- Submissions:
  - GET `/submissions` — public list of submissions (published or found_* when exposed by service)
  - GET `/submissions/mine` — list submissions created by the current user (Auth required)
  - GET `/submissions/summary` — summary counts (roles: admin only)
  - GET `/submissions/{id}` — get a single submission (404 if not visible)
  - GET `/submissions/{id}/age-progression[?years=N]` — returns `{ "url": "..." }` to a cached/progressed image
  - POST `/submissions` — multipart/form‑data create; requires at least 3 images
    - Fields: `title`, `full_name`, `dob?`, `gender?`, `race?`, `height?`, `weight?`, `province?`, `description?`,
      `last_seen_address?`, `last_seen_place_id?`, `last_seen_lat?`, `last_seen_lng?`, `images[]` (>=3, image/*)
  - PUT `/submissions/{id}` — update (owner or admin)
  - DELETE `/submissions/{id}` — delete (owner or admin)
- Static files: GET `/files/...` — serves uploaded content (images, age progression cache)

## Age progression service
Service implementation: [api/app/services/age_progression_service.py](api/app/services/age_progression_service.py)

- Tries one or more Hugging Face Spaces (default priority: `akhaliq/Photo-to-Older`, then `akhaliq/Face-Aging`).
- Selects an age group based on `target_age` or elapsed years since missing.
- Enhances and caches outputs under `files/age_progression` as `ap_{submissionId}_{years}[_<bucket>].jpg`.
- Returns an absolute URL pointing to the cached asset via `/files/age_progression/...`.
- Environment can override Spaces via `AGE_PROGRESSION_SPACES` or `AGE_PROGRESSION_SPACE`.

## Frontend features
- Public submission detail page at `/submissions/:id` with image gallery, metadata, map tile (Google Maps) and commenting rules (non‑admins only).
- Admin dashboard heat map at `/dashboard/heat-map` showing intensity overlays for:
  - Missing (published), Found Alive, Found Deceased.
  - Requires Google Maps API key; uses `last_seen_lat`/`last_seen_lng` from submissions for overlays.
- Uses `runtimeConfig.public` for API base, site URL, and Google Maps settings.

## Authentication
- Current implementation: local JWT (HS256) tokens. See [api/app/auth/local_auth.py](api/app/auth/local_auth.py) and dependency wiring in [api/app/auth/dependencies.py](api/app/auth/dependencies.py).
- Auth endpoints: see [api/app/api/controllers/auth_controller.py](api/app/api/controllers/auth_controller.py)
  - POST `/auth/register` — create account (returns access and refresh tokens)
  - POST `/auth/login` — login with email/password (returns tokens)
  - POST `/auth/refresh` — refresh access token using refresh token
  - GET `/me` — current user info (requires Authorization: Bearer <access_token>)

Quick test with curl (after running the API):
```bash
# Register (or use /auth/login)
curl -sS -X POST http://localhost:8000/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"test@example.com","password":"Passw0rd!","first_name":"Test","last_name":"User"}'

# Login
token=$(curl -sS -X POST http://localhost:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"test@example.com","password":"Passw0rd!"}' | jq -r .access_token)

# Call /me with JWT
curl -H "Authorization: Bearer $token" http://localhost:8000/me
```

## Environment variables

### Backend (.env)
```ini
DB_URL=postgresql+psycopg2://USER:PASS@HOST:PORT/DBNAME
DB_URL_ASYNC=postgresql+asyncpg://USER:PASS@HOST:PORT/DBNAME
# Local JWT auth (see api/app/auth/local_auth.py)
JWT_SECRET_KEY=change-me
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
CORS_ORIGINS=["http://localhost:3000"]
AGE_PROGRESSION_SPACES=akhaliq/Photo-to-Older,akhaliq/Face-Aging
AGE_PROGRESSION_SPACE=akhaliq/Face-Aging
```

### Frontend (.env)
```ini
NUXT_BASE_API_URL=http://localhost:8000
NUXT_HOME_URL=/
NUXT_PUBLIC_SITE_URL=http://localhost:3000
NUXT_GOOGLE_MAPS_API_KEY=your_google_maps_key
NUXT_GOOGLE_MAPS_MAP_ID=optional_map_id
NUXT_ENV_MODE=development
```

## Development workflow tips
- Start backend first so frontend can call the API.
- Uploaded files are saved under `api/files/...` and served at `http://localhost:8000/files/...`.
- Check backend logs in `api/logs/app.log` (rotates at 10 MB, retains 14 days).
- If Auth0 isn’t configured yet, public endpoints (`/health`, `/submissions`, `/submissions/{id}`) still work. Protected ones (`/me`, `/submissions/mine`, admin routes) will require a token.

## Building for production
### Backend
- Use a production Postgres. Apply migrations: `alembic upgrade head`. Run with Uvicorn/Gunicorn and a process manager.

### Frontend
- Static generation: `npm run generate:dev` (or adjust for prod) then serve `.output/public` with any static server (e.g., `npx serve .output/public`).
- Ensure `NUXT_BASE_API_URL` points at your deployed API.

## Troubleshooting
- Postgres role errors (role "postgres" does not exist): see [api/README.md#troubleshooting](api/README.md#troubleshooting) for alternatives using your OS user or creating the role.
- Port already in use (8000/3000): change the port (`uvicorn ... --port 8080`, or `nuxt dev --port 5173`).
- Age progression fails: the service will cache an enhanced original if Spaces are unavailable. Verify outbound internet and `gradio_client`.
- Google Maps not loading: set `NUXT_GOOGLE_MAPS_API_KEY` and ensure billing is enabled; optionally set `NUXT_GOOGLE_MAPS_MAP_ID`.

## More details
- Backend: see [api/README.md](api/README.md) for a beginner‑friendly, step‑by‑step backend guide with acceptance checks.
- Frontend: see [frontend/README.md](frontend/README.md) for Nuxt commands. Useful scripts in [frontend/package.json](frontend/package.json): `dev`, `dev:lan`, `dev:fast`, `build`, `generate:dev`, `preview`, `postinstall`, `format`, `format:check`.

## Acceptance
- Backend: `uvicorn app.main:app --reload` runs at http://localhost:8000; migrations apply; `/health` reachable; `/docs` and `/swagger.json` load.
- Frontend: `npm run dev` serves at http://localhost:3000, can load a submission page, and admin heat map (with proper auth and API key) renders.
- Age progression: `GET /submissions/{id}/age-progression` returns JSON with a `url` pointing to `/files/age_progression/...` once a valid submission has images.