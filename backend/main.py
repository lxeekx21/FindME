from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from config.settings import get_settings
from routers.health import router as health_router
from routers.auth import router as auth_router
from routers.reports import router as submissions_router
from routers.admin import router as admin_router
from routers.comments import router as comments_router
import logging
import sys
import os

settings = get_settings()

# Configure logging: console + rotating file under ./logs
logger.remove()
logger.add(sys.stderr, level=settings.LOG_LEVEL)
# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)
logger.add(
    "logs/app.log",
    level=settings.LOG_LEVEL,
    rotation="10 MB",
    retention="14 days",
    compression="zip",
    enqueue=True,
)

# Route stdlib logging (e.g., uvicorn, sqlalchemy) through Loguru
class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        logger.bind(logger_name=record.name).opt(depth=6, exception=record.exc_info).log(
            level, record.getMessage()
        )

logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "sqlalchemy"):
    logging.getLogger(name).handlers = []
    logging.getLogger(name).propagate = True

app = FastAPI(
    title="FindME API",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/swagger.json",
)

app.add_middleware (
    CORSMiddleware,
    allow_origins=["https://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# CORS
origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else []
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded files
os.makedirs("files", exist_ok=True)
app.mount("/files", StaticFiles(directory="files"), name="files")

# Routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(submissions_router)
app.include_router(admin_router)
app.include_router(comments_router)


@app.get("/")
async def root():
    logger.info("Root endpoint called")
    return {"name": "missing-person-api"}
