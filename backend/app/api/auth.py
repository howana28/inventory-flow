from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, Cookie
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import COOKIE_NAME, CurrentUser, create_session, current_user, delete_session, parse_permissions, verify_password
from app.models import User
from app.schemas import LoginIn

router=APIRouter(prefix="/auth",tags=["auth"])


def user_dict(user: User):
    return {"id":user.id,"name":user.name,"email":user.email,"role":user.role,"permissions":parse_permissions(user.permissions),"active":user.active}

@router.post("/login")
def login(body: LoginIn,response: Response,db: Session=Depends(get_db)):
    user=db.scalar(select(User).where(User.email==body.email.lower().strip()))
    if not user or not user.active or not verify_password(body.password,user.password_hash): raise HTTPException(401,"E-mail ou senha inválidos.")
    token=create_session(db,user)
    response.set_cookie(COOKIE_NAME,token,httponly=True,samesite="lax",secure=settings.cookie_secure,max_age=settings.session_hours*3600,path="/")
    return {"user":user_dict(user)}

@router.post("/logout")
def logout(response: Response,if_session: str|None=Cookie(default=None,alias=COOKIE_NAME),db: Session=Depends(get_db)):
    delete_session(db,if_session); response.delete_cookie(COOKIE_NAME,path="/"); return {"ok":True}

@router.get("/me")
def me(user: CurrentUser=Depends(current_user)):
    return {"user":user.__dict__}
