from __future__ import annotations

from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import auth, counting, dashboard, history, integrations, preparation, users, validation
from app.core.database import Base, SessionLocal, engine
from app.services.demo import seed_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_database(db)
    yield


def create_app() -> FastAPI:
    app=FastAPI(title="InventoryFlow API",version="1.0.0",docs_url="/api/docs",openapi_url="/api/openapi.json",lifespan=lifespan)
    api_prefix="/api/v1"
    for router in [auth.router,dashboard.router,preparation.router,counting.router,validation.router,history.router,users.router,integrations.router]: app.include_router(router,prefix=api_prefix)

    @app.get("/api/v1/health")
    def health():return {"status":"ok","service":"inventoryflow"}

    static=Path(__file__).resolve().parents[1]/"static"
    if static.exists():
        app.mount("/_next",StaticFiles(directory=static/"_next"),name="next-static") if (static/"_next").exists() else None
        assets=static/"assets"
        if assets.exists():app.mount("/assets",StaticFiles(directory=assets),name="assets")
        @app.get("/{full_path:path}",include_in_schema=False)
        def frontend(full_path:str):
            candidate=static/full_path
            if candidate.is_dir():candidate=candidate/"index.html"
            elif not candidate.suffix:candidate=static/full_path/"index.html"
            if candidate.exists() and candidate.is_file():return FileResponse(candidate)
            fallback=static/"index.html"
            return FileResponse(fallback) if fallback.exists() else {"service":"InventoryFlow API","frontend":"not built"}
    return app

app=create_app()
