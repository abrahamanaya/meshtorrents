from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from database import Base


class Model3D(Base):
    __tablename__ = "models_3d"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    author = Column(String(255), nullable=False)
    license = Column(String(50), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    tags = Column(String(500), nullable=True)
    infohash = Column(String(64), unique=True, index=True, nullable=False)
    source_uri = Column(Text, nullable=False)
    stl_preview_url = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AffiliateLink(Base):
    __tablename__ = "affiliate_links"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    affiliate_url = Column(Text, nullable=False)
    image_url = Column(Text, nullable=True)
    price_hint = Column(String(50), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    clicks = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SystemSettings(Base):
    __tablename__ = "system_settings"

    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=True)
