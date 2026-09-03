from __future__ import annotations

import secrets
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.core.security import CurrentUser, require_permission
from app.models import AppSetting, SyncLog
from app.schemas import ProviderIn, ScenarioIn
from app.services.demo import load_scenario
from app.services.integrations import bling_authorize_url, exchange_code, get_setting, set_setting, status, sync_catalog

router=APIRouter(prefix="/integrations",tags=["integrations"])

@router.get("")
def integrations(_:CurrentUser=Depends(require_permission("INTEGRACOES")),db:Session=Depends(get_db)):
    payload=status(db); logs=list(db.scalars(select(SyncLog).order_by(SyncLog.created_at.desc()).limit(12)))
    payload["sync_history"]=[{"provider":x.provider,"status":x.status,"processed":x.processed,"created":x.created,"updated":x.updated,"failures":x.failures,"duration_ms":x.duration_ms,"created_at":x.created_at.isoformat()} for x in logs]
    return payload

@router.post("/provider")
def provider(body:ProviderIn,_:CurrentUser=Depends(require_permission("INTEGRACOES")),db:Session=Depends(get_db)):
    value=body.provider.lower()
    if value not in {"demo","bling"}:raise HTTPException(400,"Provider inválido.")
    if value=="bling":
        if not settings.allow_external_connections:raise HTTPException(403,"Conexões externas estão desabilitadas neste ambiente.")
        if not get_setting(db,"bling_access_token"):raise HTTPException(409,"Conecte uma conta Bling antes de ativar este provider.")
    set_setting(db,"erp_provider",value);db.commit();return {"provider":value}

@router.post("/sync")
def sync(_:CurrentUser=Depends(require_permission("INTEGRACOES")),db:Session=Depends(get_db)):
    try:return {"sync":sync_catalog(db)}
    except Exception as e:raise HTTPException(400,str(e))

@router.get("/bling/oauth/start")
def oauth_start(_:CurrentUser=Depends(require_permission("INTEGRACOES")),db:Session=Depends(get_db)):
    state=secrets.token_urlsafe(24);set_setting(db,"bling_oauth_state",state);db.commit()
    try:return {"authorize_url":bling_authorize_url(state)}
    except Exception as e:raise HTTPException(400,str(e))

@router.get("/bling/callback",response_class=HTMLResponse)
def oauth_callback(code:str,state:str,db:Session=Depends(get_db)):
    expected=get_setting(db,"bling_oauth_state")
    if not expected or state!=expected:raise HTTPException(400,"Estado OAuth inválido.")
    try:exchange_code(db,code);set_setting(db,"erp_provider","bling");set_setting(db,"bling_oauth_state","");db.commit()
    except Exception as e:raise HTTPException(400,str(e))
    return "<html><body style='font-family:system-ui;padding:40px'><h2>Bling conectado</h2><p>Você pode fechar esta janela e voltar ao InventoryFlow.</p></body></html>"

@router.post("/demo/scenario")
def scenario(body:ScenarioIn,user:CurrentUser=Depends(require_permission("INTEGRACOES")),db:Session=Depends(get_db)):
    try:inv=load_scenario(db,body.scenario,user.id);return {"inventory":{"id":inv.id,"code":inv.code,"label":inv.label,"status":inv.status}}
    except Exception as e:raise HTTPException(400,str(e))
