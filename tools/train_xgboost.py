import sys
import os

# Setup paths to import services and modelador logic
sys.path.append("/home/bruno/Documentos/SPDI/services")
sys.path.append("/home/bruno/Documentos/SPDI/services/modelador/app")

# Set environment variables for local connection
os.environ["MINIO_HOST"] = "localhost"
os.environ["DATABASE_URL"] = "postgresql://user:password@localhost:5432/mydb"
os.environ["DB_MINIO_USER"] = "admin"
os.environ["DB_MINIO_PASS"] = "Masterkey2026"

from modelador import EntrenarModeloXGBoost

if __name__ == "__main__":
    nro = 4
    print(f"Iniciando entrenamiento local de XGBoost versión {nro}...")
    EntrenarModeloXGBoost(nro)
    print(f"Entrenamiento y registro de la versión {nro} completados!")
