from __future__ import annotations

import base64
import json
import time
from datetime import datetime, timedelta
from urllib.parse import urlencode, urlparse

import requests
from cryptography.fernet import Fernet
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.time import utcnow
from app.models import AppSetting, Product, SyncLog
from app.services.demo import sync_demo_catalog

BLING_API="https://api.bling.com.br/Api/v3"
BLING_AUTHORIZE="https://www.bling.com.br/Api/v3/oauth/authorize"
BLING_TOKEN=f"{BLING_API}/oauth/token"


def get_setting(db: Session,key: str,default: str="") -> str:
    row=db.get(AppSetting,key); return row.value if row else default


def set_setting(db: Session,key: str,value: str) -> None:
    row=db.get(AppSetting,key)
    if row: row.value=value
    else: db.add(AppSetting(key=key,value=value))
    db.flush()


def _fernet() -> Fernet:
    if not settings.token_encryption_key:
        raise RuntimeError("TOKEN_ENCRYPTION_KEY é obrigatório para armazenar tokens externos.")
    return Fernet(settings.token_encryption_key.encode())


def encrypt_token(value: str) -> str: return _fernet().encrypt(value.encode()).decode()
def decrypt_token(value: str) -> str: return _fernet().decrypt(value.encode()).decode()


def database_safe_info() -> dict:
    url=settings.database_url
    parsed=urlparse(url.replace("postgresql+psycopg","postgresql"))
    if url.startswith("sqlite"):
        return {"type":"SQLite","host":"local","database":url.split("///")[-1],"status":"connected"}
    return {"type":parsed.scheme or "PostgreSQL","host":parsed.hostname or "configured","database":parsed.path.strip("/") or "configured","status":"connected"}


def status(db: Session) -> dict:
    provider=get_setting(db,"erp_provider",settings.erp_provider)
    last=db.scalar(select(SyncLog).order_by(SyncLog.created_at.desc()))
    has_tokens=bool(get_setting(db,"bling_access_token"))
    return {
        "database":database_safe_info(),
        "erp":{
            "provider":provider,
            "allow_external_connections":settings.allow_external_connections,
            "bling_configured":bool(settings.bling_client_id and settings.bling_client_secret and settings.token_encryption_key),
            "bling_connected":has_tokens,
        },
        "last_sync": sync_dict(last) if last else None,
    }


def sync_dict(row: SyncLog) -> dict:
    return {"id":row.id,"provider":row.provider,"status":row.status,"processed":row.processed,"created":row.created,"updated":row.updated,"failures":row.failures,"duration_ms":row.duration_ms,"created_at":row.created_at.isoformat()}


def sync_catalog(db: Session) -> dict:
    provider=get_setting(db,"erp_provider",settings.erp_provider)
    start=time.perf_counter()
    try:
        if provider=="demo":
            processed,created,updated=sync_demo_catalog(db); failures=0
        elif provider=="bling":
            processed,created,updated,failures=_sync_bling(db)
        else: raise RuntimeError("Provider ERP desconhecido.")
        status_value="SUCCESS"
    except Exception as exc:
        processed=created=updated=0; failures=1; status_value="FAILED"
        log=SyncLog(provider=provider,status=status_value,failures=1,duration_ms=int((time.perf_counter()-start)*1000),details=json.dumps({"error":str(exc)},ensure_ascii=False)); db.add(log); db.commit(); raise
    log=SyncLog(provider=provider,status=status_value,processed=processed,created=created,updated=updated,failures=failures,duration_ms=int((time.perf_counter()-start)*1000)); db.add(log); db.commit(); return sync_dict(log)


def bling_authorize_url(state: str) -> str:
    if not settings.allow_external_connections: raise RuntimeError("Conexões externas estão desabilitadas neste ambiente.")
    if not settings.bling_client_id: raise RuntimeError("BLING_CLIENT_ID não configurado.")
    return BLING_AUTHORIZE+"?"+urlencode({"response_type":"code","client_id":settings.bling_client_id,"state":state,"redirect_uri":settings.bling_redirect_uri})


def exchange_code(db: Session, code: str) -> None:
    basic=base64.b64encode(f"{settings.bling_client_id}:{settings.bling_client_secret}".encode()).decode()
    r=requests.post(BLING_TOKEN,headers={"Authorization":f"Basic {basic}","Content-Type":"application/x-www-form-urlencoded","Accept":"1.0"},data={"grant_type":"authorization_code","code":code,"redirect_uri":settings.bling_redirect_uri},timeout=30)
    r.raise_for_status(); data=r.json(); _save_tokens(db,data)


def _save_tokens(db: Session,data: dict) -> None:
    set_setting(db,"bling_access_token",encrypt_token(data["access_token"]))
    if data.get("refresh_token"): set_setting(db,"bling_refresh_token",encrypt_token(data["refresh_token"]))
    set_setting(db,"bling_expires_at",(utcnow()+timedelta(seconds=int(data.get("expires_in",21600))-60)).isoformat())
    db.commit()


def _refresh_access_token(db: Session) -> str:
    encrypted_refresh=get_setting(db,"bling_refresh_token")
    if not encrypted_refresh:
        raise RuntimeError("Refresh token do Bling não disponível.")
    refresh=decrypt_token(encrypted_refresh)
    basic=base64.b64encode(f"{settings.bling_client_id}:{settings.bling_client_secret}".encode()).decode()
    r=requests.post(BLING_TOKEN,headers={"Authorization":f"Basic {basic}","Content-Type":"application/x-www-form-urlencoded","Accept":"1.0"},data={"grant_type":"refresh_token","refresh_token":refresh},timeout=30)
    r.raise_for_status(); _save_tokens(db,r.json())
    return decrypt_token(get_setting(db,"bling_access_token"))


def _access_token(db: Session, force_refresh: bool=False) -> str:
    encrypted=get_setting(db,"bling_access_token")
    if not encrypted: raise RuntimeError("Bling não conectado.")
    expires=get_setting(db,"bling_expires_at")
    if force_refresh or (expires and datetime.fromisoformat(expires) <= utcnow()):
        return _refresh_access_token(db)
    return decrypt_token(encrypted)


def _bling_get(db: Session, token: str, path: str, params: dict | None=None) -> tuple[dict,str]:
    r=requests.get(f"{BLING_API}{path}",headers={"Authorization":f"Bearer {token}","Accept":"application/json"},params=params,timeout=30)
    if r.status_code==401:
        token=_access_token(db,force_refresh=True)
        r=requests.get(f"{BLING_API}{path}",headers={"Authorization":f"Bearer {token}","Accept":"application/json"},params=params,timeout=30)
    r.raise_for_status()
    return r.json(),token


def _extract_balance(record: dict) -> int:
    candidates=["saldoFisicoTotal","saldoVirtualTotal","saldo","estoqueAtual","quantidade"]
    for key in candidates:
        value=record.get(key)
        if isinstance(value,(int,float)):
            return max(int(value),0)
        if isinstance(value,str):
            try:return max(int(float(value.replace(",","."))),0)
            except Exception:pass
    saldos=record.get("saldos")
    if isinstance(saldos,list):
        total=0
        for row in saldos:
            if isinstance(row,dict):total+=_extract_balance(row)
        return max(total,0)
    return 0


def _fetch_bling_balances(db: Session, token: str, records: list[dict]) -> tuple[dict[str,int],str]:
    balances:dict[str,int]={}
    id_to_sku={str(x.get("id")):x["sku"] for x in records if x.get("id") is not None}
    skus=[x["sku"] for x in records]
    for offset in range(0,len(skus),80):
        chunk=skus[offset:offset+80]
        params={"filtroSaldoEstoque":1}
        for idx,sku in enumerate(chunk):params[f"codigos[{idx}]"]=sku
        try:
            payload,token=_bling_get(db,token,"/estoques/saldos",params)
            for row in payload.get("data") or []:
                product=row.get("produto") if isinstance(row.get("produto"),dict) else {}
                sku=str(row.get("codigo") or product.get("codigo") or "").strip()
                if not sku:
                    product_id=str(row.get("idProduto") or product.get("id") or "")
                    sku=id_to_sku.get(product_id,"")
                if sku:balances[sku]=_extract_balance(row)
        except Exception:
            # Mantém o catálogo sincronizável mesmo se a conta não disponibilizar
            # o endpoint de saldos. Nesse caso o snapshot recebe saldo 0 para o lote.
            pass
        time.sleep(.38)
    return balances,token


def _sync_bling(db: Session) -> tuple[int,int,int,int]:
    token=_access_token(db); page=1; processed=created=updated=failures=0; records:list[dict]=[]
    while page<=100:
        payload,token=_bling_get(db,token,"/produtos",{"pagina":page,"limite":100})
        rows=payload.get("data") or []
        if not rows:break
        for raw in rows:
            sku=str(raw.get("codigo") or raw.get("id") or "").strip()
            if not sku:continue
            records.append({
                "id":raw.get("id"),"sku":sku,
                "ean":str(raw.get("gtin") or f"BLING-{raw.get('id')}")[:32],
                "name":str(raw.get("nome") or "Produto Bling")[:220],
                "brand":str((raw.get("marca") or {}).get("nome") or "Bling")[:100],
                "location":str(raw.get("localizacao") or "01.01.01")[:80],
                "active":str(raw.get("situacao") or "A").upper()!="I",
            })
        page+=1
        if len(rows)<100:break
        time.sleep(.38)
    balances,token=_fetch_bling_balances(db,token,records)
    for raw in records:
        try:
            sku=raw["sku"]; p=db.scalar(select(Product).where(Product.sku==sku))
            payload={"ean":raw["ean"],"name":raw["name"],"brand":raw["brand"],"location":raw["location"],"system_stock":balances.get(sku,0),"active":raw["active"]}
            if p:
                for k,v in payload.items():setattr(p,k,v)
                updated+=1
            else:
                db.add(Product(sku=sku,**payload));created+=1
            processed+=1
        except Exception:
            failures+=1
    db.commit();return processed,created,updated,failures

