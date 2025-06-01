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
    """
    Inicializa las tablas necesarias para el módulo de usuarios.
    Crea las tablas de usuarios y roles si no existen.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Crear tabla de roles
        cur.execute("""
                    CREATE TABLE IF NOT EXISTS roles
                    (
                        id
                        SERIAL
                        PRIMARY
                        KEY,
                        nombre
                        VARCHAR
                    (
                        50
                    ) UNIQUE NOT NULL,
                        descripcion TEXT,
                        permisos TEXT[], -- Array de permisos como strings
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)

        # Crear tabla de usuarios
        cur.execute("""
                    CREATE TABLE IF NOT EXISTS usuarios
                    (
                        id
                        SERIAL
                        PRIMARY
                        KEY,
                        nombre
                        VARCHAR
                    (
                        100
                    ) NOT NULL,
                        email VARCHAR
                    (
                        100
                    ) UNIQUE NOT NULL,
                        password_hash VARCHAR
                    (
                        255
                    ) NOT NULL,
                        activo BOOLEAN DEFAULT TRUE,
                        rol_id INTEGER REFERENCES roles
                    (
                        id
                    ),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)

        # Insertar roles por defecto si no existen
        cur.execute("SELECT COUNT(*) FROM roles")
        if cur.fetchone()[0] == 0:
            roles_default = [
                ('admin', 'Administrador General',
                 ['ver:todos', 'crear:todos', 'actualizar:todos', 'eliminar:todos', 'gestionar:usuarios']),
                ('admin_inventario', 'Administrador de Inventario',
                 ['ver:stock', 'actualizar:stock', 'ver:compras', 'crear:compras', 'ver:informes']),
                ('vendedor', 'Vendedor', ['ver:pacientes', 'crear:ventas', 'ver:stock', 'actualizar:stock_minimo']),
                ('cajero', 'Cajero', ['procesar:pagos', 'ver:ventas', 'imprimir:facturas']),
            ]

            for nombre, descripcion, permisos in roles_default:
                cur.execute(
                    "INSERT INTO roles (nombre, descripcion, permisos) VALUES (%s, %s, %s)",
                    (nombre, descripcion, permisos)
                )

        conn.commit()
        print("Base de datos inicializada correctamente para módulo usuarios")

    except Exception as e:
        print(f"Error al inicializar la base de datos: {e}")
        conn.rollback()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()