from fastapi import APIRouter, HTTPException, Response, Depends, Query
from typing import List, Optional
from app.models import (
    Compra, CompraCreate, DetalleCompra, NotaCredito, NotaCreditoCreate,
    Proveedor, ProveedorCreate
)
from app.database import get_connection
from app.kafka_producer import enviar_evento
from app.security import validate_token
from datetime import datetime
import uuid

router = APIRouter()

# ========================= COMPRAS =========================

@router.post("/", response_model=Compra, status_code=201)
def crear_compra(compra: CompraCreate, current_user_payload: dict = Depends(validate_token)):
    """Crear una nueva compra con sus detalles"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        total = sum(detalle.subtotal for detalle in compra.detalles)
        cur.execute("""
            INSERT INTO compras (proveedor_id, nombre_proveedor, fecha_compra, numero_factura, 
                               total, observaciones, estado, fecha_creacion) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
        """, (
            compra.proveedor_id, compra.nombre_proveedor, compra.fecha_compra,
            compra.numero_factura, total, compra.observaciones, 'PENDIENTE',
            datetime.now().isoformat()
        ))
        compra_id = cur.fetchone()[0]

        detalles_creados = []
        for detalle in compra.detalles:
            cur.execute("""
                INSERT INTO detalle_compras (compra_id, producto_id, nombre_producto, 
                                           cantidad, precio_unitario, subtotal)
                VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
            """, (
                compra_id, detalle.producto_id, detalle.nombre_producto,
                detalle.cantidad, detalle.precio_unitario, detalle.subtotal
            ))
            detalle_id = cur.fetchone()[0]
            detalles_creados.append(DetalleCompra(
                id=detalle_id,
                compra_id=compra_id,
                **detalle.model_dump()
            ))

        conn.commit()

        compra_completa = Compra(
            id=compra_id,
            proveedor_id=compra.proveedor_id,
            nombre_proveedor=compra.nombre_proveedor,
            fecha_compra=compra.fecha_compra,
            numero_factura=compra.numero_factura,
            total=total,
            observaciones=compra.observaciones,
            estado='PENDIENTE',
            fecha_creacion=datetime.now().isoformat(),
            detalles=detalles_creados
        )

        evento_kafka = {
            "accion": "COMPRA_CREADA",
            "compra": compra_completa.model_dump(),
            "usuario": current_user_payload.get("sub", "unknown")
        }
        enviar_evento("compras-events", evento_kafka)

        return compra_completa

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear compra: {str(e)}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@router.get("/", response_model=List[Compra])
def listar_compras(
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    fecha_desde: Optional[str] = Query(None, description="Fecha desde (YYYY-MM-DD)"),
    fecha_hasta: Optional[str] = Query(None, description="Fecha hasta (YYYY-MM-DD)"),
    current_user_payload: dict = Depends(validate_token)
):
    """Listar compras con filtros opcionales"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        query = "SELECT * FROM compras WHERE 1=1"
        params = []

        if estado:
            query += " AND estado = %s"
            params.append(estado)

        if fecha_desde:
            query += " AND fecha_compra >= %s"
            params.append(fecha_desde)

        if fecha_hasta:
            query += " AND fecha_compra <= %s"
            params.append(fecha_hasta)

        query += " ORDER BY fecha_creacion DESC"

        cur.execute(query, params)
        compras_db = cur.fetchall()

        compras_lista = []
        for compra_dict in compras_db:
            cur.execute("SELECT * FROM detalle_compras WHERE compra_id = %s", (compra_dict['id'],))
            detalles_db = cur.fetchall()
            detalles_lista = [DetalleCompra(**detalle_dict) for detalle_dict in detalles_db]
            compras_lista.append(Compra(**compra_dict, detalles=detalles_lista))

        return compras_lista

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@router.get("/{compra_id}", response_model=Compra)
def obtener_compra(compra_id: int, current_user_payload: dict = Depends(validate_token)):
    """Obtener una compra específica con sus detalles"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM compras WHERE id = %s", (compra_id,))
        compra_db = cur.fetchone()
        if not compra_db:
            raise HTTPException(status_code=404, detail=f"Compra con ID {compra_id} no encontrada")

        cur.execute("SELECT * FROM detalle_compras WHERE compra_id = %s", (compra_id,))
        detalles_db = cur.fetchall()
        detalles_lista = [DetalleCompra(**detalle_dict) for detalle_dict in detalles_db]

        return Compra(**compra_db, detalles=detalles_lista)

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@router.put("/{compra_id}/estado")
def actualizar_estado_compra(
    compra_id: int,
    nuevo_estado: str,
    current_user_payload: dict = Depends(validate_token)
):
    """Actualizar el estado de una compra"""
    estados_validos = ['PENDIENTE', 'RECIBIDA', 'CANCELADA']
    if nuevo_estado not in estados_validos:
        raise HTTPException(status_code=400, detail=f"Estado inválido. Debe ser uno de: {estados_validos}")

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM compras WHERE id = %s", (compra_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail=f"Compra con ID {compra_id} no encontrada")

        cur.execute("UPDATE compras SET estado = %s WHERE id = %s", (nuevo_estado, compra_id))
        conn.commit()

        evento_kafka = {
            "accion": "COMPRA_ESTADO_ACTUALIZADO",
            "compra_id": compra_id,
            "nuevo_estado": nuevo_estado,
            "usuario": current_user_payload.get("sub", "unknown")
        }
        enviar_evento("compras-events", evento_kafka)

        return {"mensaje": f"Estado de compra actualizado a {nuevo_estado}"}

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

# ========================= NOTAS DE CRÉDITO =========================

@router.post("/notas-credito", response_model=NotaCredito, status_code=201)
def crear_nota_credito(nota: NotaCreditoCreate, current_user_payload: dict = Depends(validate_token)):
    """Crear una nota de crédito"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM compras WHERE id = %s", (nota.compra_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail=f"Compra con ID {nota.compra_id} no encontrada")

        numero_nota = f"NC-{uuid.uuid4().hex[:8].upper()}-{datetime.now().strftime('%Y%m%d')}"
        cur.execute("""
            INSERT INTO notas_credito (compra_id, numero_nota, motivo, monto, observaciones, 
                                     fecha_creacion, estado)
            VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
        """, (
            nota.compra_id, numero_nota, nota.motivo, nota.monto,
            nota.observaciones, datetime.now().isoformat(), 'PENDIENTE'
        ))

        nota_id = cur.fetchone()[0]
        conn.commit()

        nota_completa = NotaCredito(
            id=nota_id,
            numero_nota=numero_nota,
            fecha_creacion=datetime.now().isoformat(),
            estado='PENDIENTE',
            **nota.model_dump()
        )

        evento_kafka = {
            "accion": "NOTA_CREDITO_CREADA",
            "nota_credito": nota_completa.model_dump(),
            "usuario": current_user_payload.get("sub", "unknown")
        }
        enviar_evento("compras-events", evento_kafka)

        return nota_completa

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@router.get("/notas-credito", response_model=List[NotaCredito])
def listar_notas_credito(current_user_payload: dict = Depends(validate_token)):
    """Listar todas las notas de crédito"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM notas_credito ORDER BY fecha_creacion DESC")
        notas_db = cur.fetchall()
        return [NotaCredito(**nota_dict) for nota_dict in notas_db]

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@router.put("/notas-credito/{nota_id}/aplicar")
def aplicar_nota_credito(nota_id: int, current_user_payload: dict = Depends(validate_token)):
    """Aplicar una nota de crédito"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, estado FROM notas_credito WHERE id = %s", (nota_id,))
        nota_db = cur.fetchone()

        if not nota_db:
            raise HTTPException(status_code=404, detail=f"Nota de crédito con ID {nota_id} no encontrada")
        if nota_db["estado"] != "PENDIENTE":
            raise HTTPException(status_code=400, detail="Solo se pueden aplicar notas pendientes")

        cur.execute("UPDATE notas_credito SET estado = 'APLICADA' WHERE id = %s", (nota_id,))
        conn.commit()

        evento_kafka = {
            "accion": "NOTA_CREDITO_APLICADA",
            "nota_credito_id": nota_id,
            "usuario": current_user_payload.get("sub", "unknown")
        }
        enviar_evento("compras-events", evento_kafka)

        return {"mensaje": f"Nota de crédito {nota_id} aplicada correctamente"}

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
