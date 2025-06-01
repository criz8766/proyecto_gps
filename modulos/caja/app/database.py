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


def init_db():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS cajas (
            id SERIAL PRIMARY KEY,
            usuario_id INTEGER NOT NULL,
            fecha_apertura TIMESTAMP NOT NULL,
            fecha_cierre TIMESTAMP,
            saldo_inicial NUMERIC(12,2) NOT NULL,
            saldo_final NUMERIC(12,2),
            estado VARCHAR(20) NOT NULL CHECK (estado IN ('abierta', 'cerrada'))
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS movimientos_caja (
            id SERIAL PRIMARY KEY,
            caja_id INTEGER REFERENCES cajas(id) ON DELETE CASCADE,
            tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('ingreso', 'egreso')),
            descripcion TEXT,
            monto NUMERIC(12,2) NOT NULL,
            fecha TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """)
        conn.commit()
    finally:
        cur.close()
        conn.close()
