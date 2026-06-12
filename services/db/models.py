from sqlalchemy import Column, Integer, String, Text, DateTime, Float, func
from datetime import datetime
from db.db import Base


class Orden(Base):
    __tablename__ = "ordenes"

    id = Column(Integer, primary_key=True)
    args = Column(Text)  # JSON en string
    status = Column(String, default="pending")
    prediccion = Column(Text, nullable=True)
    modelo_utilizado = Column(Text, nullable=True)
    username = Column(String)

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
    tipo = Column(Text)
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

# 📥 Usuario
class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password_hash= Column(String, nullable=False)
    responsable = Column(Text)
    tipo = Column(Text)
    descripcion = Column(Text)

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
class InformesClientes(Base):
    __tablename__ = "informesclientes"
    id = Column(Integer, primary_key=True)
    responsable = Column(Text)
    cliente = Column(Text)
    contenido = Column(Text) 
    created_at = Column(DateTime, default=datetime.utcnow)










