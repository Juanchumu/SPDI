from sqlalchemy import Column, Integer, String, Text, DateTime, Float, func, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from db.db import Base


class Orden(Base):
    __tablename__ = "ordenes"

    id = Column(Integer, primary_key=True)
    args = Column(Text)  # JSON en string
    status = Column(String, default="pending")
    prediccion = Column(Text, nullable=True)
    modelo_utilizado = Column(Text, nullable=True)

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
    tipo = Column(String, default="temporal_fire_net")  # temporal_fire_net | xgboost | temp_cnn
    final_loss = Column(Float)
    best_loss = Column(Float)
    pred_mean = Column(Float)
    pred_min = Column(Float)
    pred_max = Column(Float)
    
    accuracy = Column(Float)
    precision = Column(Float)
    recall = Column(Float)
    f1_score = Column(Float)
    iou = Column(Float)
    dice = Column(Float)
    dataset_size = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow) # fecha del modelo 


# 📥 Descargas realizadas
class Descargas(Base):
    __tablename__ = "descargas"
    descarga_id = Column(Integer, primary_key=True, autoincrement=True)
    nombre_imagen = Column(Text)
    dia_de_la_imagen= Column(Text)
    fecha_descarga = Column(DateTime, default=datetime.utcnow)

class WorkersLogs(Base):
    __tablename__ = "workerslogs"
    id = Column(Integer, primary_key=True)
    name = Column(Text) 
    descripcion = Column(Text)
    updated_at = Column(DateTime,server_default=func.now(),onupdate=func.now())
    created_at = Column(DateTime, default=datetime.utcnow)
class Informes(Base):
    __tablename__ = "informes"
    id = Column(Integer, primary_key=True)
    contenido = Column(Text) 
    created_at = Column(DateTime, default=datetime.utcnow)

class Cliente(Base):
    __tablename__ = "clientes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String)
    codigo_cliente = Column(String, unique=True)
    email = Column(String, nullable=True)
    telefono = Column(String, nullable=True)
    
    areas = relationship("AreaAsegurada", back_populates="cliente")
    created_at = Column(DateTime, default=datetime.utcnow)

class AreaAsegurada(Base):
    __tablename__ = "areas_aseguradas"
    id = Column(Integer, primary_key=True, autoincrement=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    nombre_lote = Column(String)
    latitud = Column(Float)
    longitud = Column(Float)
    riesgo_promedio = Column(Float, nullable=True)
    descripcion_entorno = Column(Text, nullable=True)
    
    cliente = relationship("Cliente", back_populates="areas")
    created_at = Column(DateTime, default=datetime.utcnow)
