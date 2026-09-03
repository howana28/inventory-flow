from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import CurrentUser, require_permission
from app.models import AuditLog, Inventory, InventoryItem
from app.services.inventory import inventory_dict, serialize_item

router=APIRouter(prefix="/history",tags=["history"])
@router.get("")
def history(_: CurrentUser=Depends(require_permission("HISTORICO")),db: Session=Depends(get_db)):
    rows=list(db.scalars(select(Inventory).order_by(Inventory.created_at.desc()).limit(50)))
    return {"inventories":[inventory_dict(x) for x in rows]}

@router.get("/{inventory_id}")
def detail(inventory_id: str,_: CurrentUser=Depends(require_permission("HISTORICO")),db: Session=Depends(get_db)):
    inv=db.get(Inventory,inventory_id)
    if not inv: raise HTTPException(404,"Inventário não encontrado.")
    items=list(db.scalars(select(InventoryItem).where(InventoryItem.inventory_id==inv.id).order_by(InventoryItem.location,InventoryItem.sku)))
    logs=list(db.scalars(select(AuditLog).where(AuditLog.inventory_id==inv.id).order_by(AuditLog.created_at.desc()).limit(100)))
    return {"inventory":inventory_dict(inv),"items":[serialize_item(x) for x in items],"logs":[{"action":x.action,"user_name":x.user_name,"resource":x.resource,"details":x.details,"created_at":x.created_at.isoformat()} for x in logs]}
