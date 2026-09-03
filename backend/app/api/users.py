from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import ALL_PERMISSIONS, CurrentUser, dump_permissions, hash_password, parse_permissions, require_permission
from app.models import User
from app.schemas import UserCreateIn, UserUpdateIn

router=APIRouter(prefix="/users",tags=["users"])
def data(x:User):return {"id":x.id,"name":x.name,"email":x.email,"role":x.role,"permissions":parse_permissions(x.permissions),"active":x.active,"created_at":x.created_at.isoformat()}

@router.get("")
def users(_:CurrentUser=Depends(require_permission("USUARIOS")),db:Session=Depends(get_db)):
    return {"users":[data(x) for x in db.scalars(select(User).order_by(User.name))],"permissions":ALL_PERMISSIONS}

@router.post("")
def create(body:UserCreateIn,_:CurrentUser=Depends(require_permission("USUARIOS")),db:Session=Depends(get_db)):
    if db.scalar(select(User).where(User.email==body.email.lower())):raise HTTPException(409,"E-mail já cadastrado.")
    u=User(name=body.name,email=body.email.lower(),role=body.role.upper(),permissions=dump_permissions(body.permissions),password_hash=hash_password(body.password));db.add(u);db.commit();return {"user":data(u)}

@router.patch("/{user_id}")
def update(user_id:str,body:UserUpdateIn,current:CurrentUser=Depends(require_permission("USUARIOS")),db:Session=Depends(get_db)):
    u=db.get(User,user_id)
    if not u:raise HTTPException(404,"Usuário não encontrado.")
    target_role=(body.role or u.role).upper(); target_active=u.active if body.active is None else body.active
    if u.role=="ADMIN" and (target_role!="ADMIN" or not target_active):
        admins=db.scalar(select(func.count(User.id)).where(User.role=="ADMIN",User.active==True)) or 0
        if admins<=1:raise HTTPException(409,"O sistema precisa manter pelo menos um administrador ativo.")
    if body.name is not None:u.name=body.name
    if body.role is not None:u.role=target_role
    if body.permissions is not None:u.permissions=dump_permissions(body.permissions)
    if body.active is not None:u.active=body.active
    if body.password:u.password_hash=hash_password(body.password)
    db.commit();return {"user":data(u)}
