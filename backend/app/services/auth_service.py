"""
Authentication service — JWT token creation and validation.

Token payload: { sub: user_id, email, role, exp }
Access token expires in 8 hours (configurable).
"""
from __future__ import annotations
import os
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.services.auth_store import get_user_by_id, ROLE_PERMISSIONS

# ── Config ───────────────────────────────────────────────────
SECRET_KEY      = os.getenv('JWT_SECRET', 'oly-vision-dev-secret-change-in-prod')
ALGORITHM       = 'HS256'
ACCESS_TOKEN_EXP = int(os.getenv('ACCESS_TOKEN_HOURS', '8'))  # hours

bearer_scheme = HTTPBearer(auto_error=False)


# ── Token helpers ────────────────────────────────────────────
def create_access_token(user: dict) -> str:
    exp = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXP)
    payload = {
        'sub':   str(user['id']),
        'email': user['email'],
        'role':  user['role'],
        'name':  user['name'],
        'exp':   exp,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


# ── FastAPI dependency ────────────────────────────────────────
def get_current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> dict:
    """
    Dependency — inject into any route that requires authentication.
    Returns the full user dict.
    Raises 401 if token is missing or invalid.
    """
    if not creds:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Not authenticated — provide a Bearer token',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    payload = decode_token(creds.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid or expired token',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    user = get_user_by_id(int(payload['sub']))
    if not user or not user.get('active'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='User not found or inactive',
        )

    return user


def require_role(*roles: str):
    """
    Role-guard dependency factory.
    Usage: @router.get('/...', dependencies=[Depends(require_role('admin'))])
    """
    def _check(user: dict = Depends(get_current_user)) -> dict:
        if user['role'] not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f'Access denied — requires role: {" or ".join(roles)}',
            )
        return user
    return _check


def has_permission(user: dict, page: str) -> bool:
    """Check if a user has access to a given page/resource."""
    return page in ROLE_PERMISSIONS.get(user['role'], [])
