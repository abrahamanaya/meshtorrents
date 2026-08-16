from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class Model3DBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    author: str = Field(..., min_length=1, max_length=255)
    license: str = Field(..., min_length=1, max_length=50, examples=["CC-BY-4.0"])
    category: str = Field(..., min_length=1, max_length=100)
    tags: Optional[str] = Field(default=None, description="Etiquetas separadas por coma")
    infohash: str = Field(..., min_length=1, max_length=64, description="Hash único para indexación P2P")
    source_uri: str = Field(..., min_length=1, description="Enlace o magnet link de origen")
    stl_preview_url: Optional[str] = Field(default=None, description="URL a un archivo .stl para la vista previa 3D")


class Model3DCreate(Model3DBase):
    pass


class Model3DResponse(Model3DBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class AffiliateLinkBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    category: str = Field(..., min_length=1, max_length=100, examples=["filamentos"])
    affiliate_url: str = Field(..., min_length=1, description="Enlace de afiliado de Mercado Libre")
    image_url: Optional[str] = Field(default=None, description="URL de la imagen del producto")
    price_hint: Optional[str] = Field(default=None, max_length=50, examples=["$399 MXN"])
    is_active: bool = True


class AffiliateLinkCreate(AffiliateLinkBase):
    pass


class AffiliateLinkResponse(AffiliateLinkBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    clicks: int
    created_at: datetime


class ScraperSettingsUpdate(BaseModel):
    prowlarr_url: Optional[str] = Field(default=None, min_length=1, description="URL base del servidor Prowlarr/Jackett")
    prowlarr_api_key: Optional[str] = Field(default=None, min_length=1, description="API Key alfanumérica de Prowlarr/Jackett")


class ScraperSettingsResponse(BaseModel):
    prowlarr_url: str
    prowlarr_api_key_masked: str
    scrape_interval_hours: int
    source: str = Field(description="'database' si hay overrides guardados, 'env' si usa los valores del .env")
    connection_ok: Optional[bool] = Field(default=None, description="Resultado de la última prueba de conexión")


class ScraperTriggerResponse(BaseModel):
    found: int
    imported: int
    skipped: int
    errors: List[str]
