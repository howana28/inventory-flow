from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.time import utcnow


def uid() -> str:
    return str(uuid4())


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(190), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(30), default="OPERADOR")
    permissions: Mapped[str] = mapped_column(Text, default="[]")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class AuthSession(Base):
    __tablename__ = "auth_sessions"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Product(Base):
    __tablename__ = "products"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    sku: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    ean: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(220))
    brand: Mapped[str] = mapped_column(String(100))
    location: Mapped[str] = mapped_column(String(80), index=True)
    system_stock: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class Inventory(Base):
    __tablename__ = "inventories"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    code: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    label: Mapped[str] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(30), default="CONTAGEM", index=True)
    created_by: Mapped[str] = mapped_column(String(36))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class InventoryZone(Base):
    __tablename__ = "inventory_zones"
    __table_args__ = (UniqueConstraint("inventory_id", "zone", name="uq_inventory_zone"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    inventory_id: Mapped[str] = mapped_column(ForeignKey("inventories.id", ondelete="CASCADE"), index=True)
    zone: Mapped[str] = mapped_column(String(30), index=True)
    status: Mapped[str] = mapped_column(String(30), default="DISPONIVEL")
    finalized_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    finalized_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class InventoryItem(Base):
    __tablename__ = "inventory_items"
    __table_args__ = (UniqueConstraint("inventory_id", "sku", name="uq_inventory_sku"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    inventory_id: Mapped[str] = mapped_column(ForeignKey("inventories.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[str] = mapped_column(String(36))
    sku: Mapped[str] = mapped_column(String(60), index=True)
    ean: Mapped[str] = mapped_column(String(32), index=True)
    name: Mapped[str] = mapped_column(String(220))
    brand: Mapped[str] = mapped_column(String(100))
    location: Mapped[str] = mapped_column(String(80), index=True)
    zone: Mapped[str] = mapped_column(String(30), index=True)
    snapshot_stock: Mapped[int] = mapped_column(Integer, default=0)
    counted_qty: Mapped[int | None] = mapped_column(Integer, nullable=True)
    recount_qty: Mapped[int | None] = mapped_column(Integer, nullable=True)
    difference: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="PENDENTE", index=True)
    resolution: Mapped[str] = mapped_column(String(40), default="")
    counted_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    counted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    recount_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    recount_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    note: Mapped[str] = mapped_column(Text, default="")


class ResourceLock(Base):
    __tablename__ = "resource_locks"
    __table_args__ = (UniqueConstraint("inventory_id", "scope", "resource", name="uq_resource_lock"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    inventory_id: Mapped[str] = mapped_column(String(36), index=True)
    scope: Mapped[str] = mapped_column(String(30), index=True)
    resource: Mapped[str] = mapped_column(String(80), index=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    session_id: Mapped[str] = mapped_column(String(80), index=True)
    operator_name: Mapped[str] = mapped_column(String(120))
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    inventory_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    user_name: Mapped[str] = mapped_column(String(120), default="Sistema")
    action: Mapped[str] = mapped_column(String(80), index=True)
    resource: Mapped[str] = mapped_column(String(120), default="")
    details: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class SyncLog(Base):
    __tablename__ = "sync_logs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    provider: Mapped[str] = mapped_column(String(30), default="demo")
    status: Mapped[str] = mapped_column(String(30), default="SUCCESS")
    processed: Mapped[int] = mapped_column(Integer, default=0)
    created: Mapped[int] = mapped_column(Integer, default=0)
    updated: Mapped[int] = mapped_column(Integer, default=0)
    failures: Mapped[int] = mapped_column(Integer, default=0)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    details: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class AppSetting(Base):
    __tablename__ = "app_settings"
    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    value: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
