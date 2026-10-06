import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

# Directory containing this file (backend/). Used so SQLite is not tied to the shell cwd.
_BACKEND_DIR = Path(__file__).resolve().parent

# Preferred: PostgreSQL URL in .env (example: postgresql+psycopg2://user:pass@localhost:5432/pricewise)
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
if DATABASE_URL.startswith("postgres://"):
    # Normalize legacy/Neon URLs for SQLAlchemy 2.0+
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if not DATABASE_URL:
    # Optional override; if unset, use a single stable file next to database.py (not ./ cwd).
    env_sqlite = os.getenv("SQLITE_URL", "").strip()
    if env_sqlite:
        DATABASE_URL = env_sqlite
    else:
        _db_path = (_BACKEND_DIR / "pricewise.db").resolve()
        DATABASE_URL = "sqlite:///" + _db_path.as_posix()

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine_kwargs = {
    "future": True,
    "connect_args": connect_args,
}

# Serverless PostgreSQL (such as Neon) drops idle connections after sleep;
# pool_pre_ping detects dead connections and reconnects automatically without 500 errors.
if not DATABASE_URL.startswith("sqlite"):
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 300

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
Base = declarative_base()
