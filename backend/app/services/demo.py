from __future__ import annotations

from datetime import datetime, timedelta
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.security import ALL_PERMISSIONS, dump_permissions, hash_password
from app.core.time import utcnow
from app.models import AuditLog, Inventory, InventoryItem, InventoryZone, Product, ResourceLock, SyncLog, User
from app.services.rules import calculate_difference, zone_from_location

BRANDS = ["North & Pine", "Luma Goods", "Atlas Home", "Novi Care", "Everfield", "Terra Lab"]
NOUNS = ["Shampoo", "Condicionador", "Sérum", "Hidratante", "Sabonete", "Loção", "Máscara", "Tônico", "Creme", "Óleo", "Spray", "Refil"]
LINES = ["Daily", "Balance", "Pure", "Fresh", "Botanical", "Repair", "Essential", "Active", "Calm", "Urban"]
SIZES = ["30ml", "60ml", "100ml", "120ml", "200ml", "250ml", "300ml", "500ml"]


def synthetic_catalog(size: int = 420) -> list[dict]:
    rows = []
    for i in range(1, size + 1):
        zone = ((i - 1) % 18) + 1
        shelf = (((i - 1) // 18) % 8) + 1
        bin_no = (((i - 1) // 144) % 5) + 1
        sku = f"P{i:05d}"
        # 13 dígitos, deterministicamente fictício e sem vínculo com qualquer catálogo real.
        ean = f"7909000{i:06d}"[:13]
        name = f"{NOUNS[(i-1)%len(NOUNS)]} {LINES[(i*3)%len(LINES)]} {SIZES[(i*5)%len(SIZES)]}"
        rows.append({
            "sku": sku,
            "ean": ean,
            "name": name,
            "brand": BRANDS[(i*7) % len(BRANDS)],
            "location": f"{zone:02d}.{shelf:02d}.{bin_no:02d}",
            "system_stock": (i * 13) % 47,
        })
    return rows


def ensure_demo_users(db: Session) -> None:
    presets = [
        ("Admin Demo", "admin@inventoryflow.demo", "ADMIN", ALL_PERMISSIONS),
        ("Supervisor Demo", "supervisor@inventoryflow.demo", "SUPERVISOR", ["DASHBOARD","PREPARAR_INVENTARIO","BIPAGEM","VALIDACAO","RECONTAGEM","HISTORICO"]),
        ("Operador Demo", "operator@inventoryflow.demo", "OPERADOR", ["DASHBOARD","BIPAGEM","RECONTAGEM"]),
    ]
    for name, email, role, permissions in presets:
        if not db.scalar(select(User).where(User.email == email)):
            db.add(User(name=name, email=email, role=role, permissions=dump_permissions(permissions), password_hash=hash_password("Demo123!")))
    db.commit()


def sync_demo_catalog(db: Session, size: int = 420) -> tuple[int,int,int]:
    created = updated = 0
    for item in synthetic_catalog(size):
        row = db.scalar(select(Product).where(Product.sku == item["sku"]))
        if not row:
            db.add(Product(**item)); created += 1
        else:
            row.ean=item["ean"]; row.name=item["name"]; row.brand=item["brand"]; row.location=item["location"]
            # variação determinística pequena para demonstrar sincronização sem randomizar toda execução
            row.system_stock=item["system_stock"]; row.active=True; updated += 1
    db.commit()
    return size, created, updated


def create_inventory_from_catalog(db: Session, created_by: str, label: str, code: str | None = None) -> Inventory:
    active = db.scalar(select(Inventory).where(Inventory.status.in_(["CONTAGEM","VALIDACAO"])))
    if active:
        return active
    code = code or f"INV-{utcnow().strftime('%Y%m%d-%H%M%S')}"
    inv = Inventory(code=code, label=label, status="CONTAGEM", created_by=created_by)
    db.add(inv); db.flush()
    products = list(db.scalars(select(Product).where(Product.active == True).order_by(Product.sku)))
    zones = sorted({zone_from_location(p.location) for p in products if zone_from_location(p.location) != "SEM_LOCALIZACAO"})
    for z in zones: db.add(InventoryZone(inventory_id=inv.id, zone=z))
    for p in products:
        db.add(InventoryItem(
            inventory_id=inv.id, product_id=p.id, sku=p.sku, ean=p.ean, name=p.name,
            brand=p.brand, location=p.location, zone=zone_from_location(p.location), snapshot_stock=max(p.system_stock,0),
        ))
    db.commit(); return inv


def _apply_counts(db: Session, inv: Inventory, all_zones: bool, with_recounts: bool=False):
    zones = list(db.scalars(select(InventoryZone).where(InventoryZone.inventory_id == inv.id).order_by(InventoryZone.zone)))
    selected = zones if all_zones else zones[:4]
    for z in selected:
        items = list(db.scalars(select(InventoryItem).where(InventoryItem.inventory_id == inv.id, InventoryItem.zone == z.zone).order_by(InventoryItem.sku)))
        for idx, item in enumerate(items):
            delta = 0
            if (idx + int(z.zone)) % 11 == 0: delta = -2
            elif (idx + int(z.zone)) % 17 == 0: delta = 3
            item.counted_qty = max(item.snapshot_stock + delta, 0)
            item.counted_at = utcnow(); item.status = "CONTADO"
        z.status="FINALIZADA"; z.finalized_at=utcnow()
    if all_zones:
        for item in db.scalars(select(InventoryItem).where(InventoryItem.inventory_id == inv.id)):
            counted = int(item.counted_qty or 0)
            item.difference = calculate_difference(counted, item.snapshot_stock)
            item.status = "OK" if item.difference == 0 else "DIVERGENTE"
        inv.status="VALIDACAO"
        db.flush()
        if with_recounts:
            divergent = list(db.scalars(select(InventoryItem).where(InventoryItem.inventory_id == inv.id, InventoryItem.status == "DIVERGENTE").order_by(InventoryItem.sku).limit(14)))
            for item in divergent: item.status="RECONTAGEM"; item.resolution="REQUESTED"
    db.commit()


def load_scenario(db: Session, scenario: str, user_id: str) -> Inventory:
    scenario = scenario.lower().strip()
    if scenario not in {"contagem","validacao","recontagem"}:
        raise ValueError("Cenário inválido.")
    # Limpa apenas inventários ainda operacionais. Histórico encerrado permanece.
    active_ids = [x for x in db.scalars(select(Inventory.id).where(Inventory.status != "ENCERRADO"))]
    if active_ids:
        db.execute(delete(ResourceLock).where(ResourceLock.inventory_id.in_(active_ids)))
        db.execute(delete(AuditLog).where(AuditLog.inventory_id.in_(active_ids)))
        db.execute(delete(InventoryItem).where(InventoryItem.inventory_id.in_(active_ids)))
        db.execute(delete(InventoryZone).where(InventoryZone.inventory_id.in_(active_ids)))
        db.execute(delete(Inventory).where(Inventory.id.in_(active_ids)))
        db.commit()
    inv = create_inventory_from_catalog(db, user_id, f"Inventário Demo — {scenario.title()}", f"DEMO-{scenario.upper()}")
    if scenario == "contagem": _apply_counts(db, inv, all_zones=False)
    elif scenario == "validacao": _apply_counts(db, inv, all_zones=True)
    else: _apply_counts(db, inv, all_zones=True, with_recounts=True)
    return inv


def seed_database(db: Session) -> None:
    ensure_demo_users(db)
    if (db.scalar(select(func.count(Product.id))) or 0) == 0:
        processed, created, updated = sync_demo_catalog(db)
        db.add(SyncLog(provider="demo", status="SUCCESS", processed=processed, created=created, updated=updated, failures=0, duration_ms=1280, details='{"source":"synthetic_seed"}'))
        db.commit()
    if (db.scalar(select(func.count(Inventory.id))) or 0) == 0:
        admin = db.scalar(select(User).where(User.email == "admin@inventoryflow.demo"))
        # Um inventário encerrado para enriquecer o histórico.
        hist = create_inventory_from_catalog(db, admin.id, "Inventário Demo — Agosto", "DEMO-2026-08")
        _apply_counts(db, hist, all_zones=True)
        for item in db.scalars(select(InventoryItem).where(InventoryItem.inventory_id == hist.id, InventoryItem.status == "DIVERGENTE")):
            item.status="APROVADO"; item.resolution="APPROVED_DEMO"
        hist.status="ENCERRADO"; hist.closed_at=utcnow()-timedelta(days=5); db.commit()
        load_scenario(db, "contagem", admin.id)
