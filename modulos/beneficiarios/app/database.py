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
        database=os.getenv("POSTGRES_DB", "beneficiarios"),
        user=os.getenv("POSTGRES_USER", "admin"),
        password=os.getenv("POSTGRES_PASSWORD", "admin"),
        cursor_factory=RealDictCursor  # para obtener resultados como dict
    )


def init_database():
    """
    Inicializa la base de datos creando las tablas necesarias si no existen.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Crear tabla beneficiarios si no existe
        cur.execute("""
                    CREATE TABLE IF NOT EXISTS beneficiarios
                    (
                        id
                        SERIAL
                        PRIMARY
                        KEY,
                        rut
                        VARCHAR
                    (
                        12
                    ) UNIQUE NOT NULL,
                        nombre VARCHAR
                    (
                        100
                    ) NOT NULL,
                        apellido_paterno VARCHAR
                    (
                        100
                    ) NOT NULL,
                        apellido_materno VARCHAR
                    (
                        100
                    ) NOT NULL,
                        fecha_nacimiento DATE NOT NULL,
                        telefono VARCHAR
                    (
                        20
                    ),
                        email VARCHAR
                    (
                        255
                    ),
                        direccion VARCHAR
                    (
                        200
                    ),
                        comuna VARCHAR
                    (
                        100
                    ) NOT NULL,
                        region VARCHAR
                    (
                        100
                    ) NOT NULL,
                        estado VARCHAR
                    (
                        20
                    ) DEFAULT 'activo',
                        fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """)

        # Crear índices para mejorar rendimiento en consultas frecuentes
        cur.execute("CREATE INDEX IF NOT EXISTS idx_beneficiarios_rut ON beneficiarios(rut);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_beneficiarios_estado ON beneficiarios(estado);")
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_beneficiarios_nombre ON beneficiarios(apellido_paterno, apellido_materno, nombre);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_beneficiarios_comuna ON beneficiarios(comuna);")

        conn.commit()
        print("INFO: Tablas de beneficiarios inicializadas correctamente")

    except Exception as e:
        print(f"ERROR: Error al inicializar base de datos de beneficiarios: {e}")
        conn.rollback()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()