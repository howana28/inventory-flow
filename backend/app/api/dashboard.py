from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_permission, CurrentUser
from app.services.inventory import dashboard_data

router=APIRouter(tags=["dashboard"])
@router.get("/dashboard")
def dashboard(_: CurrentUser=Depends(require_permission("DASHBOARD")),db: Session=Depends(get_db)):
    return dashboard_data(db)
