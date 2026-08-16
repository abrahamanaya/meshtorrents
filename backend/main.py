import random
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session

from apscheduler.schedulers.asyncio import AsyncIOScheduler

import models
import scraper_engine
import schemas
from config import settings
from database import Base, engine, get_db, SessionLocal
from p2p_engine import MeshP2PEngine

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MeshTorrents API",
    description="Catálogo y meta-buscador de modelos 3D comunitarios (.STL / .3MF) bajo licencias abiertas.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "service": "MeshTorrents API",
        "docs": "/docs",
        "frontend": "https://abrahamanaya.github.io/meshtorrents/",
    }


SEED_MODELS = [
    dict(
        title="Cabeza Articulada PR2",
        description="Modelo de cabeza robótica articulada, ideal para prototipado y estudio de mecanismos.",
        author="OpenRobotics",
        license="CC-BY-4.0",
        category="Herramientas",
        tags="robotica, articulado, prototipo",
        infohash="a1b2c3d4e5f60718293a4b5c6d7e8f9012345678",
        source_uri="magnet:?xt=urn:btih:a1b2c3d4e5f60718293a4b5c6d7e8f9012345678&dn=pr2_head",
        stl_preview_url="https://threejs.org/examples/models/stl/binary/pr2_head_pan.stl",
    ),
    dict(
        title="Colgante Decorativo Geométrico",
        description="Figura suspendida de bajo peso pensada para impresión rápida y decoración de interiores.",
        author="MeshCrafters",
        license="CC-BY-SA-4.0",
        category="Decoración",
        tags="geometrico, decoracion, hogar",
        infohash="b2c3d4e5f60718293a4b5c6d7e8f90123456789a",
        source_uri="magnet:?xt=urn:btih:b2c3d4e5f60718293a4b5c6d7e8f90123456789a&dn=colgante_low_poly",
        stl_preview_url="https://threejs.org/examples/models/stl/ascii/slotted_disk.stl",
    ),
    dict(
        title="Soporte de Repuesto para Bisagra",
        description="Pieza de repuesto genérica para bisagras de muebles de tamaño estándar.",
        author="RepairCommons",
        license="CC0-1.0",
        category="Repuestos",
        tags="repuesto, bisagra, mueble",
        infohash="c3d4e5f60718293a4b5c6d7e8f90123456789ab0",
        source_uri="magnet:?xt=urn:btih:c3d4e5f60718293a4b5c6d7e8f90123456789ab0&dn=soporte_bisagra",
        stl_preview_url="https://threejs.org/examples/models/stl/binary/colored.stl",
    ),
]

SEED_AFFILIATES = [
    dict(
        title="Filamento PLA Sunlu 1.75mm 1kg",
        category="filamentos",
        affiliate_url="https://www.mercadolibre.com.mx/",  # TODO: reemplazar por tu enlace de afiliado real
        image_url="https://picsum.photos/seed/pla-sunlu/400/300",
        price_hint="$399 MXN",
    ),
    dict(
        title="Resina Standard Anycubic 1L",
        category="resinas",
        affiliate_url="https://www.mercadolibre.com.mx/",  # TODO: reemplazar por tu enlace de afiliado real
        image_url="https://picsum.photos/seed/resina-anycubic/400/300",
        price_hint="$549 MXN",
    ),
    dict(
        title="Impresora 3D Creality Ender 3 V3",
        category="impresoras",
        affiliate_url="https://www.mercadolibre.com.mx/",  # TODO: reemplazar por tu enlace de afiliado real
        image_url="https://picsum.photos/seed/ender3v3/400/300",
        price_hint="$4,999 MXN",
    ),
    dict(
        title="Kit de Boquillas MK8 (10 pzas)",
        category="mantenimiento",
        affiliate_url="https://www.mercadolibre.com.mx/",  # TODO: reemplazar por tu enlace de afiliado real
        image_url="https://picsum.photos/seed/boquillas-mk8/400/300",
        price_hint="$149 MXN",
    ),
    dict(
        title="Set de Espátulas y Herramientas de Acabado",
        category="general",
        affiliate_url="https://www.mercadolibre.com.mx/",  # TODO: reemplazar por tu enlace de afiliado real
        image_url="https://picsum.photos/seed/espatulas-acabado/400/300",
        price_hint="$199 MXN",
    ),
]


@app.on_event("startup")
def seed_database() -> None:
    db = SessionLocal()
    try:
        if db.query(models.Model3D).count() == 0:
            for entry in SEED_MODELS:
                db.add(models.Model3D(**entry))
        if db.query(models.AffiliateLink).count() == 0:
            for entry in SEED_AFFILIATES:
                db.add(models.AffiliateLink(**entry))
        db.commit()
    finally:
        db.close()


scheduler = AsyncIOScheduler()


@app.on_event("startup")
def start_scheduler() -> None:
    # process_prowlarr_indexer resuelve la URL/API Key en cada ejecución (BD con fallback a .env),
    # así que actualizar la configuración desde /api/settings no requiere reiniciar el servidor.
    scheduler.add_job(
        scraper_engine.process_prowlarr_indexer,
        "interval",
        hours=settings.SCRAPE_INTERVAL_HOURS,
        id="prowlarr_scrape",
        replace_existing=True,
    )
    scheduler.start()


@app.on_event("shutdown")
def stop_scheduler() -> None:
    scheduler.shutdown(wait=False)


@app.get("/api/models", response_model=List[schemas.Model3DResponse])
def list_models(
    query: Optional[str] = Query(default=None, description="Búsqueda por texto en título, descripción, autor o tags"),
    category: Optional[str] = Query(default=None, description="Filtrar por categoría exacta"),
    db: Session = Depends(get_db),
):
    q = db.query(models.Model3D)

    if category:
        q = q.filter(models.Model3D.category == category)

    if query:
        like = f"%{query}%"
        q = q.filter(
            or_(
                models.Model3D.title.ilike(like),
                models.Model3D.description.ilike(like),
                models.Model3D.tags.ilike(like),
                models.Model3D.author.ilike(like),
            )
        )

    return q.order_by(models.Model3D.created_at.desc()).all()


@app.post("/api/models", response_model=schemas.Model3DResponse, status_code=201)
def create_model(payload: schemas.Model3DCreate, db: Session = Depends(get_db)):
    if payload.source_uri.startswith("magnet:"):
        p2p_info = MeshP2PEngine.parse_magnet(payload.source_uri)
        if not p2p_info["success"]:
            raise HTTPException(status_code=400, detail=p2p_info["error"])
        payload.infohash = p2p_info["infohash"]

    existing = (
        db.query(models.Model3D)
        .filter(models.Model3D.infohash == payload.infohash)
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Ya existe un modelo registrado con ese infohash")

    model = models.Model3D(**payload.model_dump())
    db.add(model)
    db.commit()
    db.refresh(model)
    return model


@app.get("/api/models/{model_id}", response_model=schemas.Model3DResponse)
def get_model(model_id: int, db: Session = Depends(get_db)):
    model = db.query(models.Model3D).filter(models.Model3D.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Modelo no encontrado")
    return model


@app.post("/api/affiliates", response_model=schemas.AffiliateLinkResponse, status_code=201)
def create_affiliate(payload: schemas.AffiliateLinkCreate, db: Session = Depends(get_db)):
    link = models.AffiliateLink(**payload.model_dump())
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


@app.get("/api/affiliates/random", response_model=List[schemas.AffiliateLinkResponse])
def random_affiliates(
    category: Optional[str] = Query(default=None, description="Categoría a priorizar, e.g. 'filamentos'"),
    count: int = Query(default=1, ge=1, le=10, description="Cantidad de enlaces a devolver"),
    db: Session = Depends(get_db),
):
    active_q = db.query(models.AffiliateLink).filter(models.AffiliateLink.is_active.is_(True))

    pool = active_q.filter(models.AffiliateLink.category == category).all() if category else []
    if not pool:
        # Sin coincidencias en la categoría solicitada: se usa el pool activo completo como respaldo.
        pool = active_q.all()

    if not pool:
        return []

    return random.sample(pool, k=min(count, len(pool)))


@app.get("/api/affiliates/{affiliate_id}/click")
def click_affiliate(affiliate_id: int, db: Session = Depends(get_db)):
    link = db.query(models.AffiliateLink).filter(models.AffiliateLink.id == affiliate_id).first()
    if not link:
        raise HTTPException(status_code=404, detail="Enlace de afiliado no encontrado")

    link.clicks += 1
    db.commit()

    return RedirectResponse(url=link.affiliate_url)


def _mask_api_key(key: str) -> str:
    if not key:
        return ""
    if len(key) <= 4:
        return "*" * len(key)
    return key[:4] + "*" * (len(key) - 4)


def _upsert_setting(db: Session, key: str, value: str) -> None:
    row = db.query(models.SystemSettings).filter(models.SystemSettings.key == key).first()
    if row:
        row.value = value
    else:
        db.add(models.SystemSettings(key=key, value=value))


@app.get("/api/settings", response_model=schemas.ScraperSettingsResponse)
def get_settings(db: Session = Depends(get_db)):
    url, api_key = scraper_engine.get_effective_prowlarr_settings(db)
    return schemas.ScraperSettingsResponse(
        prowlarr_url=url,
        prowlarr_api_key_masked=_mask_api_key(api_key),
        scrape_interval_hours=settings.SCRAPE_INTERVAL_HOURS,
        source="database" if scraper_engine.has_database_overrides(db) else "env",
    )


@app.post("/api/settings", response_model=schemas.ScraperSettingsResponse)
async def update_settings(payload: schemas.ScraperSettingsUpdate, db: Session = Depends(get_db)):
    if payload.prowlarr_url is not None:
        _upsert_setting(db, scraper_engine.PROWLARR_URL_KEY, payload.prowlarr_url.rstrip("/"))
    if payload.prowlarr_api_key is not None:
        _upsert_setting(db, scraper_engine.PROWLARR_API_KEY_KEY, payload.prowlarr_api_key)
    db.commit()

    url, api_key = scraper_engine.get_effective_prowlarr_settings(db)
    connection_ok = await scraper_engine.test_prowlarr_connection(url, api_key)

    return schemas.ScraperSettingsResponse(
        prowlarr_url=url,
        prowlarr_api_key_masked=_mask_api_key(api_key),
        scrape_interval_hours=settings.SCRAPE_INTERVAL_HOURS,
        source="database" if scraper_engine.has_database_overrides(db) else "env",
        connection_ok=connection_ok,
    )


@app.post("/api/scraper/trigger", response_model=schemas.ScraperTriggerResponse)
async def trigger_scraper(db: Session = Depends(get_db)):
    return await scraper_engine.process_prowlarr_indexer(db)