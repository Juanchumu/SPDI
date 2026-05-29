from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from db.db import Base


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

# 📦 Modelos disponibles
class Modelos(Base):
    __tablename__ = "modelos"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow) # fecha del modelo 


# 📥 Descargas realizadas
class Descargas(Base):
    __tablename__ = "descargas"
    descarga_id = Column(Integer, primary_key=True, autoincrement=True)
    nombre_imagen = Column(Text)
    dia_de_la_imagen= Column(Text)
    fecha_descarga = Column(DateTime, default=datetime.utcnow)




