from __future__ import annotations

import io
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.time import utcnow
from app.core.database import get_db
from app.core.security import CurrentUser, require_permission
from app.models import InventoryItem
from app.schemas import ApproveIn, BrowserSessionIn, RecountIn, RecountRequestIn
from app.services.audit import log_action
from app.services.inventory import active_inventory, close_inventory, consolidate_validation, inventory_dict, serialize_item, validation_summary
from app.services.locks import acquire, active_locks, heartbeat, release
from app.services.rules import calculate_difference

router=APIRouter(tags=["validation","recount"])
RECOUNT_SCOPE="RECOUNT"

def _active(db):
    inv=active_inventory(db)
    if not inv: raise HTTPException(409,"Nenhum inventário em andamento.")
    return inv

@router.get("/validation")
def validation(_: CurrentUser=Depends(require_permission("VALIDACAO")),db: Session=Depends(get_db)):
    inv=_active(db); items=list(db.scalars(select(InventoryItem).where(InventoryItem.inventory_id==inv.id).order_by(InventoryItem.status,InventoryItem.location,InventoryItem.sku)))
    return {"inventory":inventory_dict(inv),"summary":validation_summary(db,inv.id),"items":[serialize_item(x) for x in items]}

@router.post("/validation/consolidate")
def consolidate(user: CurrentUser=Depends(require_permission("VALIDACAO")),db: Session=Depends(get_db)):
    inv=_active(db)
    try:return {"summary":consolidate_validation(db,inv,user)}
    except Exception as e: raise HTTPException(409,str(e))

@router.post("/validation/recount")
def request_recount(body: RecountRequestIn,user: CurrentUser=Depends(require_permission("VALIDACAO")),db: Session=Depends(get_db)):
    inv=_active(db); changed=0
    for sku in dict.fromkeys(body.skus):
        item=db.scalar(select(InventoryItem).where(InventoryItem.inventory_id==inv.id,InventoryItem.sku==sku))
        if item and item.status=="DIVERGENTE": item.status="RECONTAGEM"; item.resolution="REQUESTED"; item.note=body.note; changed+=1
    log_action(db,"RECOUNT_REQUESTED",user,inv.id,details={"count":changed,"skus":body.skus[:50]}); db.commit(); return {"changed":changed,"summary":validation_summary(db,inv.id)}

@router.post("/validation/approve")
def approve(body: ApproveIn,user: CurrentUser=Depends(require_permission("VALIDACAO")),db: Session=Depends(get_db)):
    inv=_active(db); changed=0
    for sku in dict.fromkeys(body.skus):
        item=db.scalar(select(InventoryItem).where(InventoryItem.inventory_id==inv.id,InventoryItem.sku==sku))
        if item and item.status=="DIVERGENTE": item.status="APROVADO"; item.resolution="APPROVED"; item.note=body.note; changed+=1
    log_action(db,"DIVERGENCE_APPROVED",user,inv.id,details={"count":changed}); db.commit(); return {"changed":changed,"summary":validation_summary(db,inv.id)}

@router.post("/inventories/{inventory_id}/close")
def close(inventory_id: str,user: CurrentUser=Depends(require_permission("PREPARAR_INVENTARIO")),db: Session=Depends(get_db)):
    inv=_active(db)
    if inv.id!=inventory_id: raise HTTPException(404,"Inventário não encontrado.")
    try: close_inventory(db,inv,user); return {"ok":True}
    except Exception as e: raise HTTPException(409,str(e))

@router.get("/recounts/pending")
def pending(session_id: str=Query(default=""),user: CurrentUser=Depends(require_permission("RECONTAGEM")),db: Session=Depends(get_db)):
    inv=_active(db); locks={x.resource:x for x in active_locks(db,inv.id,RECOUNT_SCOPE)}
    items=list(db.scalars(select(InventoryItem).where(InventoryItem.inventory_id==inv.id,InventoryItem.status=="RECONTAGEM").order_by(InventoryItem.location,InventoryItem.sku)))
    out=[]
    for item in items:
        d=serialize_item(item); lock=locks.get(item.sku); mine=bool(lock and lock.user_id==user.id and lock.session_id==session_id)
        d.update({"available":lock is None or mine,"reserved_by_me":mine,"reserved_by":lock.operator_name if lock else ""}); out.append(d)
    return {"inventory":inventory_dict(inv),"items":out,"total":len(out),"available":sum(1 for x in out if x["available"]),"lock_ttl_seconds":settings.recount_lock_ttl_seconds}

@router.post("/recounts/{sku}/reserve")
def reserve_recount(sku: str,body: BrowserSessionIn,user: CurrentUser=Depends(require_permission("RECONTAGEM")),db: Session=Depends(get_db)):
    inv=_active(db); item=db.scalar(select(InventoryItem).where(InventoryItem.inventory_id==inv.id,InventoryItem.sku==sku,InventoryItem.status=="RECONTAGEM"))
    if not item: raise HTTPException(409,"Este SKU não está mais aguardando recontagem.")
    lock=acquire(db,inv.id,RECOUNT_SCOPE,sku,user,body.session_id,settings.recount_lock_ttl_seconds)
    if not lock:
        other={x.resource:x for x in active_locks(db,inv.id,RECOUNT_SCOPE)}.get(sku); raise HTTPException(409,f"SKU reservado por {other.operator_name if other else 'outro operador'}.")
    log_action(db,"RECOUNT_RESERVED",user,inv.id,sku); db.commit(); return {"ok":True,"item":serialize_item(item)}

@router.post("/recounts/{sku}/heartbeat")
def beat_recount(sku: str,body: BrowserSessionIn,user: CurrentUser=Depends(require_permission("RECONTAGEM")),db: Session=Depends(get_db)):
    inv=_active(db); row=heartbeat(db,inv.id,RECOUNT_SCOPE,sku,user,body.session_id,settings.recount_lock_ttl_seconds)
    if not row: raise HTTPException(409,"A reserva desta recontagem não pertence mais a esta sessão.")
    db.commit(); return {"ok":True}

@router.post("/recounts/{sku}/release")
def release_recount(sku: str,body: BrowserSessionIn,user: CurrentUser=Depends(require_permission("RECONTAGEM")),db: Session=Depends(get_db)):
    inv=_active(db); ok=release(db,inv.id,RECOUNT_SCOPE,sku,user,body.session_id); db.commit(); return {"ok":ok}

@router.post("/recounts/{sku}")
def submit_recount(sku: str,body: RecountIn,user: CurrentUser=Depends(require_permission("RECONTAGEM")),db: Session=Depends(get_db)):
    inv=_active(db)
    if not heartbeat(db,inv.id,RECOUNT_SCOPE,sku,user,body.session_id,settings.recount_lock_ttl_seconds): raise HTTPException(409,"Reserve este SKU antes de confirmar.")
    item=db.scalar(select(InventoryItem).where(InventoryItem.inventory_id==inv.id,InventoryItem.sku==sku,InventoryItem.status=="RECONTAGEM"))
    if not item: raise HTTPException(409,"Este SKU não está mais aguardando recontagem.")
    item.recount_qty=body.quantity; item.counted_qty=body.quantity; item.recount_by=user.id; item.recount_at=utcnow(); item.note=body.note
    item.difference=calculate_difference(body.quantity,item.snapshot_stock)
    resolved=item.difference==0
    item.status="OK" if resolved else "DIVERGENTE"; item.resolution="RECOUNT_OK" if resolved else "RECOUNT_DIVERGENT"
    release(db,inv.id,RECOUNT_SCOPE,sku,user,body.session_id); log_action(db,"RECOUNT_SUBMITTED",user,inv.id,sku,{"quantity":body.quantity,"difference":item.difference,"resolved":resolved}); db.commit()
    return {"resolved":resolved,"difference":item.difference,"item":serialize_item(item)}

@router.post("/locks/release-session")
def release_browser_locks(body: BrowserSessionIn,user: CurrentUser=Depends(require_permission("DASHBOARD")),db: Session=Depends(get_db)):
    from app.services.locks import release_session
    count=release_session(db,user.id,body.session_id); db.commit(); return {"released":count}

@router.get("/exports/validation.xlsx")
def export_validation(_: CurrentUser=Depends(require_permission("VALIDACAO")),db: Session=Depends(get_db)):
    inv=_active(db); items=list(db.scalars(select(InventoryItem).where(InventoryItem.inventory_id==inv.id).order_by(InventoryItem.location,InventoryItem.sku)))
    wb=Workbook(); ws=wb.active; ws.title="InventoryFlow"; ws.append(["SKU","EAN","Produto","Marca","Localização","Sistema","Contado","Diferença","Status","Resolução"])
    for x in items: ws.append([x.sku,x.ean,x.name,x.brand,x.location,x.snapshot_stock,x.counted_qty,x.difference,x.status,x.resolution])
    for col in ws.columns: ws.column_dimensions[col[0].column_letter].width=min(max(len(str(c.value or "")) for c in col)+2,42)
    stream=io.BytesIO(); wb.save(stream); stream.seek(0)
    return StreamingResponse(stream,media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",headers={"Content-Disposition":"attachment; filename=inventoryflow_validation.xlsx"})
