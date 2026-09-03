from __future__ import annotations

from datetime import datetime
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Inventory, InventoryItem, InventoryZone, Product
from app.core.time import utcnow
from app.services.audit import log_action
from app.services.demo import create_inventory_from_catalog
from app.services.rules import calculate_difference, classify_difference


def active_inventory(db: Session) -> Inventory | None:
    return db.scalar(select(Inventory).where(Inventory.status.in_(["CONTAGEM","VALIDACAO"])).order_by(Inventory.created_at.desc()))


def start_inventory(db: Session, user, label: str) -> Inventory:
    if active_inventory(db):
        raise ValueError("Já existe um inventário em andamento.")
    inv = create_inventory_from_catalog(db, user.id, label)
    log_action(db,"INVENTORY_STARTED",user,inv.id,inv.code,{"label":label}); db.commit(); return inv


def serialize_item(item: InventoryItem) -> dict:
    diff = item.difference
    return {
        "sku":item.sku,"ean":item.ean,"name":item.name,"brand":item.brand,
        "location":item.location,"zone":item.zone,"snapshot_stock":item.snapshot_stock,
        "counted_qty":item.counted_qty,"recount_qty":item.recount_qty,"difference":diff,
        "status":item.status,"difference_label":classify_difference(diff) if diff is not None else "PENDENTE",
        "resolution":item.resolution,"note":item.note,
    }


def dashboard_data(db: Session) -> dict:
    inv=active_inventory(db)
    catalog=db.scalar(select(func.count(Product.id)).where(Product.active==True)) or 0
    history=db.scalar(select(func.count(Inventory.id)).where(Inventory.status=="ENCERRADO")) or 0
    if not inv:
        return {"catalog":catalog,"history":history,"inventory":None,"zones":0,"zones_done":0,"items":0,"divergences":0,"recounts":0}
    zones=db.scalar(select(func.count(InventoryZone.id)).where(InventoryZone.inventory_id==inv.id)) or 0
    zones_done=db.scalar(select(func.count(InventoryZone.id)).where(InventoryZone.inventory_id==inv.id,InventoryZone.status=="FINALIZADA")) or 0
    items=db.scalar(select(func.count(InventoryItem.id)).where(InventoryItem.inventory_id==inv.id)) or 0
    divergences=db.scalar(select(func.count(InventoryItem.id)).where(InventoryItem.inventory_id==inv.id,InventoryItem.status=="DIVERGENTE")) or 0
    recounts=db.scalar(select(func.count(InventoryItem.id)).where(InventoryItem.inventory_id==inv.id,InventoryItem.status=="RECONTAGEM")) or 0
    return {"catalog":catalog,"history":history,"inventory":inventory_dict(inv),"zones":zones,"zones_done":zones_done,"items":items,"divergences":divergences,"recounts":recounts}


def inventory_dict(inv: Inventory) -> dict:
    return {"id":inv.id,"code":inv.code,"label":inv.label,"status":inv.status,"created_at":inv.created_at.isoformat(),"closed_at":inv.closed_at.isoformat() if inv.closed_at else None}


def consolidate_validation(db: Session, inv: Inventory, user) -> dict:
    pending_zones=db.scalar(select(func.count(InventoryZone.id)).where(InventoryZone.inventory_id==inv.id,InventoryZone.status!="FINALIZADA")) or 0
    if pending_zones:
        raise ValueError(f"Ainda existem {pending_zones} ruas de contagem não finalizadas.")
    items=list(db.scalars(select(InventoryItem).where(InventoryItem.inventory_id==inv.id)))
    for item in items:
        counted=int(item.counted_qty or 0)
        item.difference=calculate_difference(counted,item.snapshot_stock)
        item.status="OK" if item.difference==0 else "DIVERGENTE"
        item.resolution=""
    inv.status="VALIDACAO"
    log_action(db,"VALIDATION_CONSOLIDATED",user,inv.id,details={"items":len(items)}); db.commit()
    return validation_summary(db,inv.id)


def validation_summary(db: Session, inventory_id: str) -> dict:
    items=list(db.scalars(select(InventoryItem).where(InventoryItem.inventory_id==inventory_id)))
    counts={"OK":0,"DIVERGENTE":0,"RECONTAGEM":0,"APROVADO":0,"PENDENTE":0,"CONTADO":0}
    for i in items: counts[i.status]=counts.get(i.status,0)+1
    return {"total":len(items),**{k.lower():v for k,v in counts.items()}}


def close_inventory(db: Session, inv: Inventory, user) -> None:
    unresolved=db.scalar(select(func.count(InventoryItem.id)).where(InventoryItem.inventory_id==inv.id,InventoryItem.status.in_(["DIVERGENTE","RECONTAGEM","PENDENTE","CONTADO"]))) or 0
    if unresolved: raise ValueError(f"Ainda existem {unresolved} itens sem resolução final.")
    inv.status="ENCERRADO"; inv.closed_at=utcnow(); log_action(db,"INVENTORY_CLOSED",user,inv.id); db.commit()
