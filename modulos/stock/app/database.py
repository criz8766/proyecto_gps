import psycopg2
import os


def get_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "postgres"),
        database=os.getenv("POSTGRES_DB", "farmacia"),
        user=os.getenv("POSTGRES_USER", "admin"),
        password=os.getenv("POSTGRES_PASSWORD", "admin")
    )


def init_database():
    """Crea las tablas necesarias para el módulo de stock si no existen"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Crear tabla de productos si no existe
        cur.execute("""
                    CREATE TABLE IF NOT EXISTS productos
                    (
                        id
                        SERIAL
                        PRIMARY
                        KEY,
                        codigo
                        VARCHAR
                    (
                        50
                    ) UNIQUE NOT NULL,
                        nombre VARCHAR
                    (
                        200
                    ) NOT NULL,
                        descripcion TEXT,
                        categoria VARCHAR
                    (
                        100
                    ) NOT NULL,
                        precio_venta DECIMAL
                    (
                        10,
                        2
                    ) NOT NULL DEFAULT 0,
                        metodo_precio VARCHAR
                    (
                        50
                    ) DEFAULT 'ULTIMA_COMPRA',
                        requiere_receta BOOLEAN DEFAULT FALSE,
                        es_psicotropico BOOLEAN DEFAULT FALSE,
                        stock_minimo INTEGER DEFAULT 0,
                        stock_maximo INTEGER,
                        estado VARCHAR
                    (
                        20
                    ) DEFAULT 'ACTIVO',
                        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        fecha_actualizacion TIMESTAMP
                        )
                    """)

        # Crear tabla de bodegas si no existe
        cur.execute("""
                    CREATE TABLE IF NOT EXISTS bodegas
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
                        descripcion TEXT,
                        ubicacion VARCHAR
                    (
                        200
                    ),
                        activa BOOLEAN DEFAULT TRUE,
                        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)

        # Crear tabla de lotes si no existe
        cur.execute("""
                    CREATE TABLE IF NOT EXISTS lotes
                    (
                        id
                        SERIAL
                        PRIMARY
                        KEY,
                        numero_lote
                        VARCHAR
                    (
                        100
                    ) NOT NULL,
                        producto_id INTEGER REFERENCES productos
                    (
                        id
                    ) ON DELETE CASCADE,
                        bodega_id INTEGER REFERENCES bodegas
                    (
                        id
                    )
                      ON DELETE CASCADE,
                        fecha_vencimiento DATE,
                        precio_compra DECIMAL
                    (
                        10,
                        2
                    ) NOT NULL,
                        cantidad_inicial INTEGER NOT NULL,
                        cantidad_actual INTEGER NOT NULL,
                        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE
                    (
                        numero_lote,
                        producto_id,
                        bodega_id
                    )
                        )
                    """)

        # Crear tabla de stock si no existe
        cur.execute("""
                    CREATE TABLE IF NOT EXISTS stock
                    (
                        id
                        SERIAL
                        PRIMARY
                        KEY,
                        producto_id
                        INTEGER
                        REFERENCES
                        productos
                    (
                        id
                    ) ON DELETE CASCADE,
                        bodega_id INTEGER REFERENCES bodegas
                    (
                        id
                    )
                      ON DELETE CASCADE,
                        lote_id INTEGER REFERENCES lotes
                    (
                        id
                    )
                      ON DELETE CASCADE,
                        cantidad INTEGER NOT NULL DEFAULT 0,
                        precio_costo DECIMAL
                    (
                        10,
                        2
                    ) NOT NULL DEFAULT 0,
                        fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE
                    (
                        producto_id,
                        bodega_id,
                        lote_id
                    )
                        )
                    """)

        # Crear tabla de movimientos de stock si no existe
        cur.execute("""
                    CREATE TABLE IF NOT EXISTS movimientos_stock
                    (
                        id
                        SERIAL
                        PRIMARY
                        KEY,
                        producto_id
                        INTEGER
                        REFERENCES
                        productos
                    (
                        id
                    ) ON DELETE CASCADE,
                        bodega_id INTEGER REFERENCES bodegas
                    (
                        id
                    )
                      ON DELETE CASCADE,
                        lote_id INTEGER REFERENCES lotes
                    (
                        id
                    )
                      ON DELETE CASCADE,
                        tipo_movimiento VARCHAR
                    (
                        20
                    ) NOT NULL,
                        cantidad INTEGER NOT NULL,
                        precio_unitario DECIMAL
                    (
                        10,
                        2
                    ) NOT NULL,
                        motivo TEXT,
                        documento_referencia VARCHAR
                    (
                        100
                    ),
                        usuario_id VARCHAR
                    (
                        100
                    ),
                        fecha_movimiento TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)

        # Crear tabla de alertas de stock si no existe
        cur.execute("""
                    CREATE TABLE IF NOT EXISTS alertas_stock
                    (
                        id
                        SERIAL
                        PRIMARY
                        KEY,
                        producto_id
                        INTEGER
                        REFERENCES
                        productos
                    (
                        id
                    ) ON DELETE CASCADE,
                        bodega_id INTEGER REFERENCES bodegas
                    (
                        id
                    )
                      ON DELETE CASCADE,
                        tipo_alerta VARCHAR
                    (
                        50
                    ) NOT NULL,
                        mensaje TEXT NOT NULL,
                        fecha_alerta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        activa BOOLEAN DEFAULT TRUE
                        )
                    """)

        # Crear índices para mejorar performance
        cur.execute("CREATE INDEX IF NOT EXISTS idx_productos_codigo ON productos(codigo)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_stock_producto_bodega ON stock(producto_id, bodega_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_movimientos_fecha ON movimientos_stock(fecha_movimiento)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_lotes_vencimiento ON lotes(fecha_vencimiento)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_alertas_activas ON alertas_stock(activa, fecha_alerta)")

        # Insertar bodega por defecto si no existe
        cur.execute("SELECT COUNT(*) FROM bodegas")
        if cur.fetchone()[0] == 0:
            cur.execute("""
                        INSERT INTO bodegas (nombre, descripcion, ubicacion)
                        VALUES ('Bodega Principal', 'Bodega principal de la farmacia', 'Piso 1 - Sector A')
                        """)

        conn.commit()
        print("Base de datos del módulo Stock inicializada correctamente")

    except Exception as e:
        print(f"Error al inicializar la base de datos: {e}")
        conn.rollback()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


# Función para obtener estadísticas rápidas
def get_stock_stats():
    """Obtiene estadísticas básicas del stock"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        stats = {}

        # Total de productos
        cur.execute("SELECT COUNT(*) FROM productos WHERE estado = 'ACTIVO'")
        stats['total_productos'] = cur.fetchone()[0]

        # Total de bodegas activas
        cur.execute("SELECT COUNT(*) FROM bodegas WHERE activa = TRUE")
        stats['total_bodegas'] = cur.fetchone()[0]

        # Productos con stock bajo
        cur.execute("""
                    SELECT COUNT(DISTINCT p.id)
                    FROM productos p
                             JOIN stock s ON p.id = s.producto_id
                    WHERE s.cantidad <= p.stock_minimo
                      AND p.estado = 'ACTIVO'
                    """)
        stats['productos_stock_bajo'] = cur.fetchone()[0]

        # Alertas activas
        cur.execute("SELECT COUNT(*) FROM alertas_stock WHERE activa = TRUE")
        stats['alertas_activas'] = cur.fetchone()[0]

        # Valor total del inventario
        cur.execute("""
                    SELECT COALESCE(SUM(s.cantidad * s.precio_costo), 0)
                    FROM stock s
                             JOIN productos p ON s.producto_id = p.id
                    WHERE p.estado = 'ACTIVO'
                    """)
        stats['valor_total_inventario'] = float(cur.fetchone()[0] or 0)

        return stats

    except Exception as e:
        print(f"Error al obtener estadísticas: {e}")
        return {}
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()