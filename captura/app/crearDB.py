import psycopg2
from sqlalchemy import create_engine, text

DB_NAME = "mydb"
DB_USER = "user"
DB_PASSWORD = "password"
DB_HOST = "db"

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
        # 📦 Productos
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS products (
            id TEXT PRIMARY KEY,
            name TEXT,
            fecha TEXT
        )
        """))
        
        # 📥 Descargas
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS downloads (
            product_id TEXT PRIMARY KEY,
            filepath TEXT,
            fecha_descarga TIMESTAMP
        )
        """))
        
        # 🟢 Ordenes
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS ordenes (
            id SERIAL PRIMARY KEY,
            args TEXT,
            status TEXT,
            ruta_safe TEXT,
            ruta_stack TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
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
