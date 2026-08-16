"""
MeshTorrents - Motor de Scraping y Extracción Automática de Metadatos 3D/STL
Orquesta la consulta a Prowlarr/Jackett y la importación de resultados nuevos al catálogo.
"""

from typing import Optional, Tuple

import httpx
from sqlalchemy.orm import Session

import models
from config import settings
from database import SessionLocal
from p2p_engine import fetch_prowlarr_feed

PROWLARR_URL_KEY = "prowlarr_url"
PROWLARR_API_KEY_KEY = "prowlarr_api_key"


def _get_setting(db: Session, key: str) -> Optional[str]:
    row = db.query(models.SystemSettings).filter(models.SystemSettings.key == key).first()
    return row.value if row and row.value else None


def get_effective_prowlarr_settings(db: Session) -> Tuple[str, str]:
    """Resuelve (url, api_key) priorizando los overrides guardados en SystemSettings sobre el .env."""
    url = (_get_setting(db, PROWLARR_URL_KEY) or settings.PROWLARR_URL).rstrip("/")
    api_key = _get_setting(db, PROWLARR_API_KEY_KEY) or settings.PROWLARR_API_KEY
    return url, api_key


def has_database_overrides(db: Session) -> bool:
    return _get_setting(db, PROWLARR_URL_KEY) is not None or _get_setting(db, PROWLARR_API_KEY_KEY) is not None


async def test_prowlarr_connection(url: str, api_key: str) -> bool:
    """Prueba de conectividad ligera contra la API de Prowlarr/Jackett."""
    if not api_key:
        return False
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{url}/api/v1/system/status", params={"apikey": api_key}, timeout=5.0)
            return response.status_code == 200
    except Exception:
        return False


async def process_prowlarr_indexer(db: Optional[Session] = None) -> dict:
    """
    Ejecuta un ciclo de scraping contra Prowlarr/Jackett: busca contenido STL/3D,
    descarta lo que ya existe en el catálogo (por infohash) e importa el resto como Model3D.
    """
    owns_session = db is None
    db = db or SessionLocal()
    summary = {"found": 0, "imported": 0, "skipped": 0, "errors": []}

    try:
        url, api_key = get_effective_prowlarr_settings(db)
        if not api_key:
            summary["errors"].append("No hay PROWLARR_API_KEY configurada (ni en la base de datos ni en el .env).")
            return summary

        results = await fetch_prowlarr_feed(url, api_key, query="stl 3d print")
        if results is None:
            summary["errors"].append(f"No se pudo consultar Prowlarr/Jackett en {url}.")
            return summary

        summary["found"] = len(results)

        for item in results:
            infohash = item["infohash"]
            exists = db.query(models.Model3D).filter(models.Model3D.infohash == infohash).first()
            if exists:
                summary["skipped"] += 1
                continue

            model = models.Model3D(
                title=item["title"][:255],
                description=f"Importado automáticamente desde Prowlarr/Jackett ({item.get('seeders', 0)} seeders).",
                author="Indexer Prowlarr",
                license="Verificar licencia en la fuente original",
                category="Otros",
                tags="auto-importado",
                infohash=infohash,
                source_uri=item["magnet_uri"],
                stl_preview_url=None,
            )
            db.add(model)
            summary["imported"] += 1

        db.commit()
        return summary
    finally:
        if owns_session:
            db.close()
