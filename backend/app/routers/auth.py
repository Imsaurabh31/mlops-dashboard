"""
Stage 4 — Authentication & RBAC endpoints.

POST /api/auth/login         — get JWT token
GET  /api/auth/me            — current user info
POST /api/auth/logout        — client-side token discard (stateless)
GET  /api/auth/users         — list all users (admin only)
POST /api/auth/users         — create user (admin only)
PATCH /api/auth/users/{id}   — update user (admin only)
GET  /api/auth/permissions   — what pages the current user can access
"""
from __future__ import annotations
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field, field_validator

from app.services import auth_store as store
from app.services.auth_service import (
    create_access_token, get_current_user, require_role,
)

router = APIRouter(prefix='/auth', tags=['Auth'])


# ── Request / Response schemas ───────────────────────────────
class LoginRequest(BaseModel):
    email:    str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type:   str = 'bearer'
    user:         dict


class CreateUserRequest(BaseModel):
    name:     str = Field(..., min_length=1)
    email:    str = Field(..., min_length=3)
    password: str = Field(..., min_length=6)
    role:     str = Field(..., pattern='^(admin|curator|viewer)$')


class UpdateUserRequest(BaseModel):
    name:     Optional[str] = None
    role:     Optional[str] = Field(None, pattern='^(admin|curator|viewer)$')
    active:   Optional[bool] = None
    password: Optional[str] = Field(None, min_length=6)


# ── Endpoints ────────────────────────────────────────────────

@router.post('/login', response_model=LoginResponse)
def login(body: LoginRequest):
    """
    Authenticate with email + password.
    Returns a JWT access token and user info.
    """
    user = store.get_user_by_email(body.email)

    if not user or not store.verify_password(body.password, user['password']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid email or password',
        )

    if not user.get('active'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Account is inactive — contact your administrator',
        )

    # Update last login
    from app.services.auth_store import _ts
    user['last_login'] = _ts()

    token = create_access_token(user)
    return LoginResponse(
        access_token=token,
        user=store.safe_user(user),
    )


@router.get('/me')
def me(current_user: dict = Depends(get_current_user)):
    """Return current authenticated user info."""
    return store.safe_user(current_user)


@router.get('/permissions')
def permissions(current_user: dict = Depends(get_current_user)):
    """Return list of pages/resources the current user can access."""
    from app.services.auth_store import ROLE_PERMISSIONS
    return {
        'role':        current_user['role'],
        'permissions': ROLE_PERMISSIONS.get(current_user['role'], []),
    }


@router.post('/logout')
def logout(current_user: dict = Depends(get_current_user)):
    """
    Logout — JWT is stateless so we just confirm.
    The client should discard the token.
    """
    return {'message': f'Goodbye {current_user["name"]} — token discarded on client'}


@router.get('/users')
def list_users(current_user: dict = Depends(require_role('admin'))):
    """List all users — admin only."""
    return [store.safe_user(u) for u in store.USERS]


@router.post('/users', status_code=status.HTTP_201_CREATED)
def create_user(
    body: CreateUserRequest,
    current_user: dict = Depends(require_role('admin')),
):
    """Create a new user — admin only."""
    if store.get_user_by_email(body.email):
        raise HTTPException(status_code=409, detail=f'Email {body.email} already exists')

    new_user = {
        'id':         store.next_user_id(),
        'name':       body.name.strip(),
        'email':      body.email.strip().lower(),
        'password':   store.hash_password(body.password),
        'role':       body.role,
        'active':     True,
        'created_at': store._ts(),
        'last_login': None,
    }
    store.USERS.append(new_user)
    return store.safe_user(new_user)


@router.patch('/users/{user_id}')
def update_user(
    user_id: int,
    body: UpdateUserRequest,
    current_user: dict = Depends(require_role('admin')),
):
    """Update user details — admin only."""
    user = store.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail='User not found')

    # Prevent admin from deactivating themselves
    if user_id == current_user['id'] and body.active is False:
        raise HTTPException(status_code=400, detail='You cannot deactivate your own account')

    if body.name     is not None: user['name']     = body.name.strip()
    if body.role     is not None: user['role']     = body.role
    if body.active   is not None: user['active']   = body.active
    if body.password is not None: user['password'] = store.hash_password(body.password)

    return store.safe_user(user)
