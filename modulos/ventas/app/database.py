import psycopg2
import os
from psycopg2.extras import RealDictCursor

def get_connection():
    """
    Establece y retorna una conexión a la base de datos PostgreSQL.
    Usa variables de entorno para configuración.
    """
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "postgres"),
        database=os.getenv("POSTGRES_DB", "farmacia"),
        user=os.getenv("POSTGRES_USER", "admin"),
        password=os.getenv("POSTGRES_PASSWORD", "admin"),
        cursor_factory=RealDictCursor  # para obtener resultados como dict
    )