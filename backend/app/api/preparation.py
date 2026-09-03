from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_permission, CurrentUser
from app.models import Product
from app.schemas import InventoryStartIn
from app.services.integrations import sync_catalog
from app.services.inventory import active_inventory, inventory_dict, start_inventory

router=APIRouter(tags=["preparation"])

@router.get("/preparation")
def info(_: CurrentUser=Depends(require_permission("PREPARAR_INVENTARIO")),db: Session=Depends(get_db)):
    inv=active_inventory(db); count=db.scalar(select(func.count(Product.id)).where(Product.active==True)) or 0
    return {"catalog_count":count,"inventory":inventory_dict(inv) if inv else None}

@router.post("/preparation/sync")
def sync(_: CurrentUser=Depends(require_permission("PREPARAR_INVENTARIO")),db: Session=Depends(get_db)):
    try:return {"sync":sync_catalog(db)}
    except Exception as e: raise HTTPException(400,str(e))

@router.post("/inventories/start")
def start(body: InventoryStartIn,user: CurrentUser=Depends(require_permission("PREPARAR_INVENTARIO")),db: Session=Depends(get_db)):
    try:return {"inventory":inventory_dict(start_inventory(db,user,body.label))}
    except Exception as e: raise HTTPException(409,str(e))
