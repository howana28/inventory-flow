from __future__ import annotations

import json
from sqlalchemy.orm import Session

from app.models import AuditLog


def log_action(db: Session, action: str, user=None, inventory_id: str | None = None, resource: str = "", details: dict | None = None):
    db.add(AuditLog(
        inventory_id=inventory_id,
        user_id=getattr(user, "id", None),
        user_name=getattr(user, "name", "Sistema"),
        action=action,
        resource=resource,
        details=json.dumps(details or {}, ensure_ascii=False),
    ))
