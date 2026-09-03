from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable
from uuid import uuid4

from fastapi import Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.time import utcnow
from app.models import AuthSession, User

COOKIE_NAME = "if_session"
PBKDF2_ITERATIONS = 310_000

ALL_PERMISSIONS = [
    "DASHBOARD",
    "PREPARAR_INVENTARIO",
    "BIPAGEM",
    "VALIDACAO",
    "RECONTAGEM",
    "HISTORICO",
    "USUARIOS",
    "INTEGRACOES",
]


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, iterations, salt_b64, digest_b64 = encoded.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(digest_b64)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, int(iterations))
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def parse_permissions(raw: str | None) -> list[str]:
    try:
        data = json.loads(raw or "[]")
        return [x for x in data if x in ALL_PERMISSIONS]
    except Exception:
        return []


def dump_permissions(values: Iterable[str]) -> str:
    clean = [p for p in ALL_PERMISSIONS if p in set(values)]
    return json.dumps(clean)


@dataclass
class CurrentUser:
    id: str
    name: str
    email: str
    role: str
    permissions: list[str]


def create_session(db: Session, user: User) -> str:
    token = str(uuid4())
    db.add(AuthSession(id=token, user_id=user.id, expires_at=utcnow() + timedelta(hours=settings.session_hours)))
    db.commit()
    return token


def delete_session(db: Session, token: str | None) -> None:
    if token:
        row = db.get(AuthSession, token)
        if row:
            db.delete(row)
            db.commit()


def current_user(
    if_session: str | None = Cookie(default=None, alias=COOKIE_NAME),
    db: Session = Depends(get_db),
) -> CurrentUser:
    if not if_session:
        raise HTTPException(401, "Sessão não autenticada.")
    session = db.get(AuthSession, if_session)
    if not session or session.expires_at < utcnow():
        if session:
            db.delete(session); db.commit()
        raise HTTPException(401, "Sessão expirada.")
    user = db.get(User, session.user_id)
    if not user or not user.active:
        raise HTTPException(401, "Usuário indisponível.")
    return CurrentUser(user.id, user.name, user.email, user.role, parse_permissions(user.permissions))


def require_permission(permission: str):
    def dependency(user: CurrentUser = Depends(current_user)) -> CurrentUser:
        if permission not in user.permissions:
            raise HTTPException(403, "Você não possui permissão para acessar este módulo.")
        return user
    return dependency
