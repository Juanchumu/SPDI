import psycopg2
from sqlalchemy import create_engine, text
import os


DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")

# Conectar a la base por defecto para crear la DB si no existe
conn = psycopg2.connect(
    database="postgres",
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST
)
conn.autocommit = True
cursor = conn.cursor()

# Crear la base de datos si no existe
cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'")
existe = cursor.fetchone()
if not existe:
    cursor.execute(f"CREATE DATABASE {DB_NAME}")

cursor.close()
conn.close()

# Conectar a la base ya creada y crear las tablas
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"
engine = create_engine(DATABASE_URL)

# Usar un contexto de transacción explícito
with engine.connect() as conn:
    # Iniciar una transacción
    trans = conn.begin()
    
    try:
        # ==========================
        # ALTER TABLES (Migraciones)
        # ==========================
        # WorkersLogs
        #conn.execute(text("""
        #ALTER TABLE workerslogs
        #ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP
        #"""))
        # Modelos | son los modelos generados automaticamente
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS modelos (
            id SERIAL PRIMARY KEY,
            name TEXT,
            tipo TEXT,
            final_loss DOUBLE PRECISION,
            best_loss DOUBLE PRECISION,
            pred_mean DOUBLE PRECISION,
            pred_min DOUBLE PRECISION,
            pred_max DOUBLE PRECISION,
            
            accuracy DOUBLE PRECISION,
            precision DOUBLE PRECISION,
            recall DOUBLE PRECISION,
            f1_score DOUBLE PRECISION,
            iou DOUBLE PRECISION,
            dice DOUBLE PRECISION,

            dataset_size INTEGER,
            
            created_at TIMESTAMP
        )
        """))
        
        # Descargas | son las descargas de los archivos de sentinel
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS descargas (
            descarga_id SERIAL PRIMARY KEY,
            nombre_imagen TEXT,
            dia_de_la_imagen TEXT,
            fecha_descarga TIMESTAMP
        )
        """))
        # Usuarios | 
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            username varchar(100) unique not null,
            password_hash varchar(255) not null,
            responsable TEXT,
            tipo TEXT,
            descripcion TEXT,
            rol TEXT DEFAULT 'cliente',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """))
        
        # Ordenes | las ordenes 
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS ordenes (
            id SERIAL PRIMARY KEY,
            args TEXT,
            status TEXT,
            prediccion TEXT,
            modelo_utilizado TEXT,
            username varchar(100),
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        )
        """))
        # Entrenamientos | los Entrenamientos 
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS entrenamientos (
            id SERIAL PRIMARY KEY,
            args TEXT,
            status TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        )
        """))
        # WorkersLogs 
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS workerslogs (
            id SERIAL PRIMARY KEY,
            name TEXT,
            descripcion TEXT,
            updated_at TIMESTAMP,
            created_at TIMESTAMP
        )
        """))
        # informes  
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS informes (
            id SERIAL PRIMARY KEY,
            contenido TEXT,
            created_at TIMESTAMP
        )
        """))
        # informes-clientes
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS informesclientes (
            id SERIAL PRIMARY KEY,
            responsable TEXT,
            cliente TEXT,
            estado TEXT,
            contenido TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        )
        """))

        # Informes-riesgo 
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS informesriesgo (
            id SERIAL PRIMARY KEY,
            responsable TEXT,
            cliente TEXT,
            estado TEXT,
            contenido TEXT,
            descripcion TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        )
        """))
        # Cliente
        conn.execute(text("""
		CREATE TABLE IF NOT EXISTS clientes (
    		id SERIAL PRIMARY KEY,
    		nombre TEXT,
    		codigo_cliente TEXT UNIQUE,
    		email TEXT,
    		telefono TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """))

        # AreaAsegurada
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS areas_aseguradas (
            id SERIAL PRIMARY KEY,
            cliente_id INTEGER REFERENCES clientes(id),
            nombre_lote TEXT,
            latitud FLOAT,
            longitud FLOAT,
            riesgo_promedio FLOAT,
            descripcion_entorno TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """))
       
        
        # Confirmar la transacción
        trans.commit()
        print("✅ Tablas creadas exitosamente")
        
    except Exception as e:
        # Si hay error, deshacer los cambios
        trans.rollback()
        print(f"❌ Error al crear tablas: {e}")
        raise
