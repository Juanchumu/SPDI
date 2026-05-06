from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from app.db import Base


class Orden(Base):
    __tablename__ = "ordenes"

    id = Column(Integer, primary_key=True)
    args = Column(Text)  # JSON en string
    status = Column(String, default="pending")

    ruta_safe = Column(Text, nullable=True)
    ruta_stack = Column(Text, nullable=True)
    prediccion = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Entrenamiento(Base):
    __tablename__ = "entrenamientos"

    id = Column(Integer, primary_key=True)
    args = Column(Text)  # JSON en string
    status = Column(String, default="pending")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# 📦 Productos disponibles (Copernicus)
class Product(Base):
    __tablename__ = "products"

    id = Column(String, primary_key=True)
    name = Column(Text)
    fecha = Column(Text)  # fecha del producto


# 📥 Descargas realizadas
class Download(Base):
    __tablename__ = "downloads"

    product_id = Column(String, primary_key=True)
    filepath = Column(Text)
    fecha_descarga = Column(DateTime, default=datetime.utcnow)
