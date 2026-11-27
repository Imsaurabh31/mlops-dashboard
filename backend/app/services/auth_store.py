"""
User store — in-memory user accounts with hashed passwords.
Replace with a real database when ready.

Roles:
  admin   — full access: all pages, create/delete users, all actions
  curator — curation + training pages only, cannot access admin panel
  viewer  — read-only: dashboard and deployment pages only
"""
from __future__ import annotations
import threading
from datetime import datetime
from typing import Dict, List, Optional
from passlib.context import CryptContext

pwd_ctx = CryptContext(schemes=['bcrypt'], deprecated='auto')

_lock        = threading.Lock()
_NEXT_USER_ID = 10


def _ts() -> str:
    return datetime.now().strftime('%Y-%m-%d %H:%M')


def hash_password(plain: str) -> str:
    return pwd_ctx.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)


# ── Seed users ───────────────────────────────────────────────
# Passwords are bcrypt hashed.  Plain-text shown in comments for demo only.
USERS: List[dict] = [
    {
        'id':         1,
        'name':       'Admin User',
        'email':      'admin@oly.com',
        'password':   hash_password('admin123'),   # plain: admin123
        'role':       'admin',
        'active':     True,
        'created_at': '2026-10-01 09:00',
        'last_login': None,
    },
    {
        'id':         2,
        'name':       'Alice Chen',
        'email':      'alice@oly.com',
        'password':   hash_password('curator123'),  # plain: curator123
        'role':       'curator',
        'active':     True,
        'created_at': '2026-10-05 10:00',
        'last_login': None,
    },
    {
        'id':         3,
        'name':       'Bob Smith',
        'email':      'bob@oly.com',
        'password':   hash_password('curator123'),
        'role':       'curator',
        'active':     True,
        'created_at': '2026-10-05 10:00',
        'last_login': None,
    },
    {
        'id':         4,
        'name':       'View User',
        'email':      'viewer@oly.com',
        'password':   hash_password('viewer123'),   # plain: viewer123
        'role':       'viewer',
        'active':     True,
        'created_at': '2026-10-10 11:00',
        'last_login': None,
    },
]

# ── RBAC permission map ──────────────────────────────────────
ROLE_PERMISSIONS: Dict[str, List[str]] = {
    'admin':   ['dashboard', 'curation', 'training', 'admin', 'deployment', 'users'],
    'curator': ['dashboard', 'curation', 'training'],
    'viewer':  ['dashboard', 'deployment'],
}


def get_user_by_email(email: str) -> Optional[dict]:
    return next((u for u in USERS if u['email'] == email), None)


def get_user_by_id(user_id: int) -> Optional[dict]:
    return next((u for u in USERS if u['id'] == user_id), None)


def next_user_id() -> int:
    global _NEXT_USER_ID
    with _lock:
        uid = _NEXT_USER_ID
        _NEXT_USER_ID += 1
    return uid


def safe_user(u: dict) -> dict:
    """Return user dict without the password hash."""
    return {k: v for k, v in u.items() if k != 'password'}
