from fastapi import APIRouter, HTTPException, Depends
from typing import List
from datetime import datetime
from app.models import (
    Caja, CajaCreate, CajaClose,
    MovimientoCaja, MovimientoCajaCreate,
    CajaResumen
)
from app.database import get_connection
from app.kafka_producer import enviar_evento
from app.security import require_permissions

router = APIRouter()


# ==================== ENDPOINTS DE CAJAS ====================

@router.get("/cajas", response_model=List[Caja])
def listar_cajas(current_user_payload: dict = Depends(require_permissions(["ver:cajas", "administrar:cajas"]))):
    """Listar todas las cajas"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
                    SELECT id,
                           usuario_id,
                           fecha_apertura,
                           fecha_cierre,
                           saldo_inicial,
                           saldo_final,
                           estado
                    FROM cajas
                    ORDER BY fecha_apertura DESC
                    """)
        cajas_db = cur.fetchall()

        return [
            Caja(**caja_row)
            for caja_row in cajas_db
        ]
    finally:
        cur.close()
        conn.close()


@router.post("/cajas", response_model=Caja, status_code=201)
def crear_caja(caja: CajaCreate,
               current_user_payload: dict = Depends(require_permissions(["crear:cajas", "administrar:cajas"]))):
    """Crear/Abrir una nueva caja"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Verificar si ya hay una caja abierta para el usuario
        cur.execute("""
                    SELECT id
                    FROM cajas
                    WHERE usuario_id = %s
                      AND estado = 'abierta'
                    """, (caja.usuario_id,))
        caja_abierta = cur.fetchone()
        if caja_abierta:
            raise HTTPException(
                status_code=400,
                detail=f"El usuario {caja.usuario_id} ya tiene una caja abierta (ID: {caja_abierta['id']})"
            )

        # Insertar nueva caja
        cur.execute("""
                    INSERT INTO cajas (usuario_id, saldo_inicial, fecha_apertura, estado)
                    VALUES (%s, %s, %s,
                            'abierta') RETURNING id, usuario_id, fecha_apertura, fecha_cierre, saldo_inicial, saldo_final, estado
                    """, (caja.usuario_id, caja.saldo_inicial, datetime.now()))

        nueva_caja_db = cur.fetchone()
        conn.commit()

        nueva_caja = Caja(**nueva_caja_db)

        # Evento Kafka
        evento_kafka = {
            "accion": "CAJA_ABIERTA",
            "caja": {
                "id": nueva_caja.id,
                "usuario_id": nueva_caja.usuario_id,
                "fecha_apertura": nueva_caja.fecha_apertura.isoformat(),
                "saldo_inicial": float(nueva_caja.saldo_inicial),
                "estado": nueva_caja.estado
            }
        }
        enviar_evento("caja-events", evento_kafka)
        return nueva_caja
    finally:
        cur.close()
        conn.close()


@router.put("/cajas/{id_caja}", response_model=Caja)
def cerrar_caja(id_caja: int, caja_close: CajaClose,
                current_user_payload: dict = Depends(require_permissions(["cerrar:cajas", "administrar:cajas"]))):
    """Cerrar una caja"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
                    SELECT id, usuario_id, fecha_apertura, saldo_inicial, estado
                    FROM cajas
                    WHERE id = %s
                    """, (id_caja,))
        caja_existente = cur.fetchone()
        if not caja_existente:
            raise HTTPException(status_code=404, detail=f"Caja con ID {id_caja} no encontrada")
        if caja_existente['estado'] != 'abierta':
            raise HTTPException(status_code=400, detail=f"La caja {id_caja} ya está cerrada")

        cur.execute("""
                    UPDATE cajas
                    SET fecha_cierre = %s,
                        saldo_final  = %s,
                        estado       = 'cerrada'
                    WHERE id = %s RETURNING id, usuario_id, fecha_apertura, fecha_cierre, saldo_inicial, saldo_final, estado
                    """, (datetime.now(), caja_close.saldo_final, id_caja))

        caja_cerrada_db = cur.fetchone()
        conn.commit()

        caja_cerrada = Caja(**caja_cerrada_db)

        evento_kafka = {
            "accion": "CAJA_CERRADA",
            "caja": {
                "id": caja_cerrada.id,
                "usuario_id": caja_cerrada.usuario_id,
                "fecha_cierre": caja_cerrada.fecha_cierre.isoformat(),
                "saldo_final": float(caja_cerrada.saldo_final),
                "estado": caja_cerrada.estado
            }
        }
        enviar_evento("caja-events", evento_kafka)
        return caja_cerrada
    finally:
        cur.close()
        conn.close()


@router.get("/cajas/{id_caja}", response_model=CajaResumen)
def obtener_caja_con_resumen(id_caja: int, current_user_payload: dict = Depends(
    require_permissions(["ver:cajas", "administrar:cajas"]))):
    """Obtener una caja específica con resumen de movimientos"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
                    SELECT id,
                           usuario_id,
                           fecha_apertura,
                           fecha_cierre,
                           saldo_inicial,
                           saldo_final,
                           estado
                    FROM cajas
                    WHERE id = %s
                    """, (id_caja,))
        caja_db = cur.fetchone()
        if not caja_db:
            raise HTTPException(status_code=404, detail=f"Caja con ID {id_caja} no encontrada")

        cur.execute("""
                    SELECT COALESCE(SUM(CASE WHEN tipo = 'ingreso' THEN monto ELSE 0 END), 0) as total_ingresos,
                           COALESCE(SUM(CASE WHEN tipo = 'egreso' THEN monto ELSE 0 END), 0)  as total_egresos,
                           COUNT(*)                                                           as cantidad_movimientos
                    FROM movimientos_caja
                    WHERE caja_id = %s
                    """, (id_caja,))
        resumen_db = cur.fetchone()

        resumen = CajaResumen(
            **caja_db,
            total_ingresos=resumen_db['total_ingresos'],
            total_egresos=resumen_db['total_egresos'],
            cantidad_movimientos=resumen_db['cantidad_movimientos']
        )
        return resumen
    finally:
        cur.close()
        conn.close()
