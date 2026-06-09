from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Build URL from individual DB env vars if not provided
    db_user = os.getenv("DB_USER") or "${POSTGRES_USER}"
    db_pass = os.getenv("DB_PASSWORD") or "${POSTGRES_PASSWORD}"
    db_host = os.getenv("DB_HOST") or "db"
    db_port = os.getenv("DB_PORT") or "5432"
    db_name = os.getenv("DB_NAME") or "${POSTGRES_DB}"
    DATABASE_URL = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()
