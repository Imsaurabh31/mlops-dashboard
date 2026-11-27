"""
SQLite database setup using SQLAlchemy.
Database file: backend/data/oly_vision.db

Provides:
  - engine      — sync engine for migrations/setup
  - SessionLocal — session factory for sync routes
  - Base        — declarative base for all models
  - get_db()    — FastAPI dependency that yields a session
"""
from __future__ import annotations
import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from typing import Generator

# ── Database path ─────────────────────────────────────────────
DATA_DIR = Path(__file__).parent.parent.parent / 'data'
DATA_DIR.mkdir(exist_ok=True)
DB_PATH  = DATA_DIR / 'oly_vision.db'
DB_URL   = f'sqlite:///{DB_PATH}'

# ── Engine ───────────────────────────────────────────────────
engine = create_engine(
    DB_URL,
    connect_args={'check_same_thread': False},  # needed for SQLite
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


# ── FastAPI dependency ────────────────────────────────────────
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
