from __future__ import annotations

from datetime import datetime, timedelta
from sqlalchemy import and_, delete, select
from sqlalchemy.orm import Session

from app.models import ResourceLock
from app.core.time import utcnow


def cleanup_expired(db: Session) -> None:
    db.execute(delete(ResourceLock).where(ResourceLock.expires_at < utcnow()))
    db.flush()


def acquire(db: Session, inventory_id: str, scope: str, resource: str, user, session_id: str, ttl_seconds: int):
    cleanup_expired(db)
    row = db.scalar(select(ResourceLock).where(and_(
        ResourceLock.inventory_id == inventory_id,
        ResourceLock.scope == scope,
        ResourceLock.resource == resource,
    )))
    expires = utcnow() + timedelta(seconds=ttl_seconds)
    if row:
        if row.user_id == user.id and row.session_id == session_id:
            row.expires_at = expires; row.updated_at = utcnow(); db.flush(); return row
        return None
    row = ResourceLock(
        inventory_id=inventory_id, scope=scope, resource=resource,
        user_id=user.id, session_id=session_id, operator_name=user.name,
        expires_at=expires,
    )
    db.add(row); db.flush(); return row


def heartbeat(db: Session, inventory_id: str, scope: str, resource: str, user, session_id: str, ttl_seconds: int):
    cleanup_expired(db)
    row = db.scalar(select(ResourceLock).where(and_(
        ResourceLock.inventory_id == inventory_id,
        ResourceLock.scope == scope,
        ResourceLock.resource == resource,
        ResourceLock.user_id == user.id,
        ResourceLock.session_id == session_id,
    )))
    if not row:
        return None
    row.expires_at = utcnow() + timedelta(seconds=ttl_seconds)
    row.updated_at = utcnow(); db.flush(); return row


def release(db: Session, inventory_id: str, scope: str, resource: str, user, session_id: str) -> bool:
    row = db.scalar(select(ResourceLock).where(and_(
        ResourceLock.inventory_id == inventory_id,
        ResourceLock.scope == scope,
        ResourceLock.resource == resource,
        ResourceLock.user_id == user.id,
        ResourceLock.session_id == session_id,
    )))
    if not row: return False
    db.delete(row); db.flush(); return True


def release_session(db: Session, user_id: str, session_id: str) -> int:
    rows = list(db.scalars(select(ResourceLock).where(and_(ResourceLock.user_id == user_id, ResourceLock.session_id == session_id))))
    for row in rows: db.delete(row)
    db.flush(); return len(rows)


def active_locks(db: Session, inventory_id: str, scope: str) -> list[ResourceLock]:
    cleanup_expired(db)
    return list(db.scalars(select(ResourceLock).where(and_(ResourceLock.inventory_id == inventory_id, ResourceLock.scope == scope))))
