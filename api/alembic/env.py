from logging.config import fileConfig
import os
import sys
from pathlib import Path
from sqlalchemy import engine_from_config, pool
from alembic import context
from dotenv import load_dotenv

# Ensure project root (parent of alembic) on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# load env from project root
load_dotenv(".env")

config = context.config

# pull DB_URL from environment if sqlalchemy.url is empty or placeholder-like
url = config.get_main_option("sqlalchemy.url", default="")
if not url or url.startswith("%(DB_URL)") or "%(" in url:
    db_url = os.getenv("DB_URL")
    if not db_url:
        raise RuntimeError(
            "DB_URL is not set in environment and sqlalchemy.url is empty; set DB_URL in .env or alembic.ini"
        )
    config.set_main_option("sqlalchemy.url", db_url)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# target metadata: use SQLAlchemy models if needed for autogenerate
from app.entities.base import metadata  # noqa: E402
from app.entities.user import User  # noqa: F401,E402
from app.entities.role import Role  # noqa: F401,E402
from app.entities.user_role import UserRole  # noqa: F401,E402
from app.entities.submission import Submission  # noqa: F401,E402

target_metadata = metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata, compare_type=True
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
