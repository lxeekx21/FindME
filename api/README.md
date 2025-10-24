FindSouth API — FastAPI Backend (JWT, Postgres, Alembic, Local Cache)

Overview
- FastAPI backend with .NET-style layering:
  - Controllers = HTTP endpoints
  - Models = Pydantic DTOs
  - Entities = SQLAlchemy ORM models
  - Repositories = DB access
  - Services = business logic
  - Auth = Local JWT verification (HS256) + role-based decorators
  - Caching = in-process TTL cache
  - Migrations = Alembic (schema + seed roles)
  - Config = Pydantic Settings + .env

Quickstart (for beginners)
Follow these steps exactly. If something fails, see Troubleshooting at the end.

1) Install prerequisites
- Git
- Python 3.11+ (check with: python3 --version)
- pip (Python package manager)
- A local PostgreSQL 16 server (installed natively)
- curl (for testing) and optionally jq
- On Windows, use Git Bash or WSL for shell commands.

2) Clone and enter the project
- git clone <your_repo_url>
- cd api

3) Start PostgreSQL (locally)
- Ensure your local PostgreSQL server is running and listening on port 5432 (or your chosen port).
  Examples:
  - macOS (Homebrew): brew services start postgresql@16
  - Ubuntu/Debian: sudo systemctl start postgresql
  - Windows: Start the PostgreSQL service from Services.msc
- Create a user/password if needed and remember the port/host.
  Default assumptions in this README use: user=postgres password=postgres db=find_south host=localhost port=5432

4) Create and activate a Python virtual environment
- python3 -m venv .venv
- source .venv/bin/activate   # Windows (Git Bash): source .venv/Scripts/activate

5) Install dependencies
- pip install -r requirements.txt
- If you plan to run the seed script with image age estimation and image augmentations, install the seed-only extras:
  - pip install -r requirements.seed.txt

6) Create your .env file
- cp .env.example .env
- Open .env in a text editor and verify/change values as needed. Example values for a local Postgres:
  DB_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/find_south
  DB_URL_ASYNC=postgresql+asyncpg://postgres:postgres@localhost:5432/find_south
  JWT_* values in .env control local auth. Ensure JWT_SECRET_KEY and expiries are set. You can run the app and obtain a token via /auth/login to call the /me endpoint.

7) Create the database (dev only)
The shell script uses environment variables (not .env) to connect. Example (adjust as needed for your local Postgres):
- chmod +x scripts/create_db.sh   # first time only
- DB_NAME=find_south DB_USER=postgres DB_PASSWORD=postgres ./scripts/create_db.sh
If you run Postgres locally with different credentials, adjust DB_NAME/DB_USER/DB_PASSWORD/DB_HOST/DB_PORT accordingly.

8) Run database migrations (schema + seed roles)
- Ensure your .env DB_URL uses a database role that exists on your local Postgres. If you see "role \"postgres\" does not exist", change the user in DB_URL (and DB_URL_ASYNC) to an existing role (often your OS username on macOS Homebrew installs), e.g.:
  DB_URL=postgresql+psycopg2://$(whoami):<password>@localhost:5432/find_south
  DB_URL_ASYNC=postgresql+asyncpg://$(whoami):<password>@localhost:5432/find_south
  Or create the role (see Troubleshooting below).
- alembic upgrade head

9) Run the app (auto-reload)
- uvicorn app.main:app --reload
The API is now available at http://localhost:8000

10) Open API docs and healthcheck
- Swagger UI: http://localhost:8000/swagger
- OpenAPI JSON: http://localhost:8000/swagger.json
- Health: http://localhost:8000/health

11) Get a JWT token (for /me and protected routes)
- Register (or login) in a new shell:
  curl -sS -X POST http://localhost:8000/auth/register \
    -H 'Content-Type: application/json' \
    -d '{"email":"test@example.com","password":"Passw0rd!","first_name":"Test","last_name":"User"}'
- Login and capture token:
  token=$(curl -sS -X POST http://localhost:8000/auth/login \
    -H 'Content-Type: application/json' \
    -d '{"email":"test@example.com","password":"Passw0rd!"}' | jq -r .access_token)
- Call /me with the token:
  curl -H "Authorization: Bearer $token" http://localhost:8000/me

Project Layout
api/
  app/
    api/controllers/
    auth/
    core/
    db/repositories/
    entities/
    models/
    services/
    main.py
  alembic/
  scripts/
    create_db.sh
    drop_create_db.sh
  alembic.ini
  .env.example
  requirements.txt
  pyproject.toml

Troubleshooting
- psql: command not found
  Install PostgreSQL client tools (psql). On macOS: brew install libpq && brew link --force libpq. On Ubuntu: sudo apt-get install postgresql-client.
- Connection refused to 5432
  Ensure Postgres is running locally and listening on the expected port.
  Examples:
    - macOS (Homebrew): brew services start postgresql@16
    - Ubuntu/Debian: sudo systemctl start postgresql
  Verify connectivity:
    psql -h localhost -U postgres -p 5432 -c 'SELECT 1;'
  Adjust host/port/user/password as needed.
- Address already in use :8000
  Another app is using the port. Either stop it or run uvicorn with a different port: uvicorn app.main:app --reload --port 8080.
- JWT errors (Invalid token)
  Ensure you include the Authorization: Bearer <access_token> header and that your JWT_* settings (secret, algorithm, expiries) match between token creation and verification.
- psycopg2 OperationalError: role "postgres" does not exist
  This means your local Postgres server doesn’t have a role named postgres. Fix one of the following ways:
  a) Use an existing local role in your .env DB_URL/DB_URL_ASYNC and in create_db.sh env vars. On macOS (Homebrew), this is often your macOS username with no password:
     DB_URL=postgresql+psycopg2://$(whoami)@localhost:5432/find_south
     DB_URL_ASYNC=postgresql+asyncpg://$(whoami)@localhost:5432/find_south
     And run: DB_USER=$(whoami) ./scripts/create_db.sh
  b) Create the postgres role (requires admin privileges):
     createuser -s postgres
     # or via psql:
     psql -d postgres -c "CREATE ROLE postgres WITH LOGIN SUPERUSER PASSWORD 'postgres';"
  After updating the role or DB_URL, re-run: alembic upgrade head.

Acceptance
- uvicorn app.main:app --reload runs app locally
- DB created via ./scripts/create_db.sh using provided env vars
- alembic upgrade head applies schema + seeds roles
- /health is public
- /auth/login returns a JWT (access + refresh)
- /me works with the JWT access token
- Role decorator enforces permissions
- Local TTL cache caches summary endpoint
