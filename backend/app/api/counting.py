from __future__ import annotations

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.time import utcnow
from app.core.database import get_db
from app.core.security import CurrentUser, require_permission
from app.models import InventoryItem, InventoryZone
from app.schemas import BrowserSessionIn, CountIn
from app.services.audit import log_action
from app.services.inventory import active_inventory, serialize_item
from app.services.locks import acquire, active_locks, heartbeat, release

router=APIRouter(prefix="/counting",tags=["counting"])
SCOPE="COUNTING"

def _active(db):
    inv=active_inventory(db)
    if not inv: raise HTTPException(409,"Nenhum inventário em andamento.")
    if inv.status!="CONTAGEM": raise HTTPException(409,"A etapa de contagem já foi concluída.")
    return inv

def _zone(db,inv_id,zone):
    row=db.scalar(select(InventoryZone).where(InventoryZone.inventory_id==inv_id,InventoryZone.zone==zone))
    if not row: raise HTTPException(404,"Rua não encontrada.")
    return row

def _zone_data(db,inv_id,zone):
    items=list(db.scalars(select(InventoryItem).where(InventoryItem.inventory_id==inv_id,InventoryItem.zone==zone).order_by(InventoryItem.location,InventoryItem.sku)))
    counted=sum(1 for x in items if x.counted_qty is not None)
    return {"zone":zone,"total":len(items),"counted":counted,"pending":len(items)-counted,"items":[serialize_item(x) for x in items]}

@router.get("/zones")
def zones(user: CurrentUser=Depends(require_permission("BIPAGEM")),db: Session=Depends(get_db)):
    inv=_active(db); locks={x.resource:x for x in active_locks(db,inv.id,SCOPE)}
    rows=list(db.scalars(select(InventoryZone).where(InventoryZone.inventory_id==inv.id).order_by(InventoryZone.zone)))
    result=[]
    for z in rows:
        total=db.scalar(select(func.count(InventoryItem.id)).where(InventoryItem.inventory_id==inv.id,InventoryItem.zone==z.zone)) or 0
        counted=db.scalar(select(func.count(InventoryItem.id)).where(InventoryItem.inventory_id==inv.id,InventoryItem.zone==z.zone,InventoryItem.counted_qty.is_not(None))) or 0
        lock=locks.get(z.zone)
        result.append({"zone":z.zone,"status":z.status,"total":total,"counted":counted,"available":lock is None,"lock":{"operator_name":lock.operator_name,"user_id":lock.user_id,"session_id":lock.session_id} if lock else None})
    return {"inventory_id":inv.id,"zones":result}

@router.post("/zones/{zone}/reserve")
def reserve_zone(zone: str,body: BrowserSessionIn,user: CurrentUser=Depends(require_permission("BIPAGEM")),db: Session=Depends(get_db)):
    inv=_active(db); z=_zone(db,inv.id,zone)
    if z.status=="FINALIZADA": raise HTTPException(409,"Esta rua já foi finalizada.")
    lock=acquire(db,inv.id,SCOPE,zone,user,body.session_id,settings.count_lock_ttl_seconds)
    if not lock:
        other={x.resource:x for x in active_locks(db,inv.id,SCOPE)}.get(zone); owner=other.operator_name if other else "outro operador"
        raise HTTPException(409,f"Rua reservada por {owner}.")
    z.status="EM_CONTAGEM"; log_action(db,"ZONE_RESERVED",user,inv.id,zone); db.commit(); return {"ok":True,"data":_zone_data(db,inv.id,zone)}

@router.post("/zones/{zone}/heartbeat")
def beat(zone: str,body: BrowserSessionIn,user: CurrentUser=Depends(require_permission("BIPAGEM")),db: Session=Depends(get_db)):
    inv=_active(db); row=heartbeat(db,inv.id,SCOPE,zone,user,body.session_id,settings.count_lock_ttl_seconds)
    if not row: raise HTTPException(409,"A reserva desta rua não pertence mais a esta sessão.")
    db.commit(); return {"ok":True}

@router.get("/zones/{zone}")
def zone_data(zone: str,_: CurrentUser=Depends(require_permission("BIPAGEM")),db: Session=Depends(get_db)):
    inv=_active(db); _zone(db,inv.id,zone); return _zone_data(db,inv.id,zone)

@router.post("/zones/{zone}/count")
def count(zone: str,body: CountIn,user: CurrentUser=Depends(require_permission("BIPAGEM")),db: Session=Depends(get_db)):
    inv=_active(db)
    if not heartbeat(db,inv.id,SCOPE,zone,user,body.session_id,settings.count_lock_ttl_seconds): raise HTTPException(409,"Reserve esta rua antes de contar.")
    code=body.code.strip().upper()
    item=db.scalar(select(InventoryItem).where(InventoryItem.inventory_id==inv.id,or_(func.upper(InventoryItem.sku)==code,func.upper(InventoryItem.ean)==code)))
    if not item: raise HTTPException(404,"Código/SKU não encontrado no snapshot.")
    if item.zone!=zone: raise HTTPException(409,f"Este produto pertence à Rua {item.zone} ({item.location}).")
    if body.mode=="replace": item.counted_qty=body.quantity
    else: item.counted_qty=int(item.counted_qty or 0)+body.quantity
    item.counted_by=user.id; item.counted_at=utcnow(); item.status="CONTADO"
    log_action(db,"ITEM_COUNTED",user,inv.id,item.sku,{"zone":zone,"quantity":item.counted_qty,"mode":body.mode}); db.commit()
    return {"item":serialize_item(item),"data":_zone_data(db,inv.id,zone)}

@router.post("/zones/{zone}/finalize")
def finalize(zone: str,body: BrowserSessionIn,user: CurrentUser=Depends(require_permission("BIPAGEM")),db: Session=Depends(get_db)):
    inv=_active(db)
    if not heartbeat(db,inv.id,SCOPE,zone,user,body.session_id,settings.count_lock_ttl_seconds): raise HTTPException(409,"A reserva desta rua não pertence mais a esta sessão.")
    z=_zone(db,inv.id,zone)
    for item in db.scalars(select(InventoryItem).where(InventoryItem.inventory_id==inv.id,InventoryItem.zone==zone,InventoryItem.counted_qty.is_(None))):
        item.counted_qty=0; item.counted_by=user.id; item.counted_at=utcnow(); item.status="CONTADO"
    z.status="FINALIZADA"; z.finalized_by=user.id; z.finalized_at=utcnow(); release(db,inv.id,SCOPE,zone,user,body.session_id)
    log_action(db,"ZONE_FINALIZED",user,inv.id,zone); db.commit(); return {"ok":True}

@router.post("/zones/{zone}/release")
def release_zone(zone: str,body: BrowserSessionIn,user: CurrentUser=Depends(require_permission("BIPAGEM")),db: Session=Depends(get_db)):
    inv=_active(db); ok=release(db,inv.id,SCOPE,zone,user,body.session_id); z=_zone(db,inv.id,zone)
    if z.status!="FINALIZADA":z.status="DISPONIVEL"
    db.commit(); return {"ok":ok}
