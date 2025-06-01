from fastapi import APIRouter, HTTPException, Response, Depends, Query
from typing import List, Optional
from datetime import datetime, date
from app.models import Venta, VentaCreate, VentaResumen
from app.database import get_connection
from app.kafka_producer import enviar_evento
from app.security import validate_token, require_role

router = APIRouter()


@router.post("/", response_model=Venta, status_code=201)
def crear_venta(
        venta: VentaCreate,
        current_user_payload: dict = Depends(validate_token)
):
    """
    Crear una nueva venta.
    Roles permitidos: admin, vendedor, cajero
    """
    # Verificar roles
    require_role(['admin', 'vendedor', 'cajero'])(current_user_payload)

    conn = get_connection()
    cur = conn.cursor()
    try:
        # Calcular totales
        subtotal = sum(detalle.subtotal for detalle in venta.detalles)
        total = subtotal - venta.descuento

        # Obtener información del usuario
        usuario_vendedor = current_user_payload.get('email', 'usuario_desconocido')

        # Insertar venta principal
        cur.execute("""
                    INSERT INTO ventas (paciente_id, paciente_rut, paciente_nombre, fecha_venta,
                                        tipo_venta, metodo_pago, subtotal, descuento, total,
                                        estado, observaciones, usuario_vendedor)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id, fecha_venta
                    """, (
                        venta.paciente_id, venta.paciente_rut, venta.paciente_nombre,
                        datetime.now(), venta.tipo_venta, venta.metodo_pago,
                        subtotal, venta.descuento, total, 'completada',
                        venta.observaciones, usuario_vendedor
                    ))

        venta_result = cur.fetchone()
        venta_id = venta_result['id']
        fecha_venta = venta_result['fecha_venta']

        # Insertar detalles de venta
        detalles_insertados = []
        for detalle in venta.detalles:
            cur.execute("""
                        INSERT INTO detalle_ventas (venta_id, producto_id, nombre_producto, cantidad,
                                                    precio_unitario, subtotal)
                        VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
                        """, (
                            venta_id, detalle.producto_id, detalle.nombre_producto,
                            detalle.cantidad, detalle.precio_unitario, detalle.subtotal
                        ))

            detalle_id = cur.fetchone()['id']
            detalles_insertados.append({
                "id": detalle_id,
                "venta_id": venta_id,
                "producto_id": detalle.producto_id,
                "nombre_producto": detalle.nombre_producto,
                "cantidad": detalle.cantidad,
                "precio_unitario": detalle.precio_unitario,
                "subtotal": detalle.subtotal
            })

        conn.commit()

        # Crear objeto venta completo para respuesta
        venta_completa = {
            "id": venta_id,
            "paciente_id": venta.paciente_id,
            "paciente_rut": venta.paciente_rut,
            "paciente_nombre": venta.paciente_nombre,
            "fecha_venta": fecha_venta,
            "tipo_venta": venta.tipo_venta,
            "metodo_pago": venta.metodo_pago,
            "subtotal": subtotal,
            "descuento": venta.descuento,
            "total": total,
            "estado": "completada",
            "observaciones": venta.observaciones,
            "usuario_vendedor": usuario_vendedor,
            "detalles": detalles_insertados
        }

        # Enviar evento a Kafka
        evento_kafka = {
            "accion": "VENTA_CREADA",
            "venta": venta_completa
        }
        enviar_evento("ventas-events", evento_kafka)

        return Venta(**venta_completa)

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear venta: {str(e)}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@router.get("/{venta_id}", response_model=Venta)
def obtener_venta_por_id(
        venta_id: int,
        current_user_payload: dict = Depends(validate_token)
):
    """
    Obtener una venta específica por ID.
    Roles permitidos: admin, vendedor, cajero
    """
    require_role(['admin', 'vendedor', 'cajero'])(current_user_payload)

    conn = get_connection()
    cur = conn.cursor()
    try:
        # Obtener venta principal
        cur.execute("""
                    SELECT id,
                           paciente_id,
                           paciente_rut,
                           paciente_nombre,
                           fecha_venta,
                           tipo_venta,
                           metodo_pago,
                           subtotal,
                           descuento,
                           total,
                           estado,
                           observaciones,
                           usuario_vendedor
                    FROM ventas
                    WHERE id = %s
                    """, (venta_id,))

        venta_data = cur.fetchone()
        if not venta_data:
            raise HTTPException(status_code=404, detail=f"Venta con ID {venta_id} no encontrada")

        # Obtener detalles de la venta
        cur.execute("""
                    SELECT id,
                           venta_id,
                           producto_id,
                           nombre_producto,
                           cantidad,
                           precio_unitario,
                           subtotal
                    FROM detalle_ventas
                    WHERE venta_id = %s
                    """, (venta_id,))

        detalles_data = cur.fetchall()

        # Construir respuesta
        venta_completa = dict(venta_data)
        venta_completa['detalles'] = [dict(detalle) for detalle in detalles_data]

        return Venta(**venta_completa)

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@router.get("/", response_model=List[VentaResumen])
def listar_ventas(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        paciente_rut: Optional[str] = None,
        estado: Optional[str] = None,
        current_user_payload: dict = Depends(validate_token)
):
    """
    Listar ventas con filtros opcionales.
    Roles permitidos: admin, vendedor, cajero
    """
    require_role(['admin', 'vendedor', 'cajero'])(current_user_payload)

    conn = get_connection()
    cur = conn.cursor()
    try:
        # Construir query dinámico
        query = """
                SELECT id, paciente_rut, paciente_nombre, fecha_venta, total, estado, tipo_venta
                FROM ventas
                WHERE 1 = 1 \
                """
        params = []

        if fecha_desde:
            query += " AND DATE(fecha_venta) >= %s"
            params.append(fecha_desde)

        if fecha_hasta:
            query += " AND DATE(fecha_venta) <= %s"
            params.append(fecha_hasta)

        if paciente_rut:
            query += " AND paciente_rut ILIKE %s"
            params.append(f"%{paciente_rut}%")

        if estado:
            query += " AND estado = %s"
            params.append(estado)

        query += " ORDER BY fecha_venta DESC LIMIT %s OFFSET %s"
        params.extend([limit, skip])

        cur.execute(query, params)
        ventas_data = cur.fetchall()

        return [VentaResumen(**dict(venta)) for venta in ventas_data]

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@router.get("/paciente/{paciente_rut}", response_model=List[VentaResumen])
def obtener_ventas_por_paciente(
        paciente_rut: str,
        current_user_payload: dict = Depends(validate_token)
):
    """
    Obtener historial de ventas de un paciente específico.
    Roles permitidos: admin, vendedor, cajero
    """
    require_role(['admin', 'vendedor', 'cajero'])(current_user_payload)

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
                    SELECT id, paciente_rut, paciente_nombre, fecha_venta, total, estado, tipo_venta
                    FROM ventas
                    WHERE paciente_rut = %s
                    ORDER BY fecha_venta DESC
                    """, (paciente_rut,))

        ventas_data = cur.fetchall()
        return [VentaResumen(**dict(venta)) for venta in ventas_data]

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@router.put("/{venta_id}/cancelar", response_model=Venta)
def cancelar_venta(
        venta_id: int,
        current_user_payload: dict = Depends(validate_token)
):
    """
    Cancelar una venta existente.
    Solo roles: admin
    """
    require_role(['admin'])(current_user_payload)

    conn = get_connection()
    cur = conn.cursor()
    try:
        # Verificar que la venta existe y está completada
        cur.execute("SELECT estado FROM ventas WHERE id = %s", (venta_id,))
        venta_actual = cur.fetchone()

        if not venta_actual:
            raise HTTPException(status_code=404, detail=f"Venta con ID {venta_id} no encontrada")

        if venta_actual['estado'] == 'cancelada':
            raise HTTPException(status_code=400, detail="La venta ya está cancelada")

        # Actualizar estado a cancelada
        cur.execute("""
                    UPDATE ventas
                    SET estado = 'cancelada'
                    WHERE id = %s
                    """, (venta_id,))

        conn.commit()

        # Obtener venta actualizada para respuesta
        return obtener_venta_por_id(venta_id, current_user_payload)

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error al cancelar venta: {str(e)}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

            @router.get("/reportes/resumen-diario")
            def obtener_resumen_diario(
                    fecha: Optional[date] = None,
                    current_user_payload: dict = Depends(validate_token)
            ):
                """
                Obtener resumen de ventas del día.
                Roles permitidos: admin, vendedor
                """
                require_role(['admin', 'vendedor'])(current_user_payload)

                if not fecha:
                    fecha = date.today()

                conn = get_connection()
                cur = conn.cursor()
                try:
                    cur.execute("""
                                SELECT COUNT(*)                                          as total_ventas,
                                       COALESCE(SUM(total), 0)                           as total_ingresos,
                                       COALESCE(AVG(total), 0)                           as promedio_venta,
                                       COUNT(CASE WHEN estado = 'completada' THEN 1 END) as ventas_completadas,
                                       COUNT(CASE WHEN estado = 'cancelada' THEN 1 END)  as ventas_canceladas
                                FROM ventas
                                WHERE DATE (fecha_venta) = %s
                                """, (fecha,))

                    resumen = cur.fetchone()

                    return {
                        "fecha": fecha,
                        "total_ventas": resumen['total_ventas'],
                        "total_ingresos": float(resumen['total_ingresos']),
                        "promedio_venta": float(resumen['promedio_venta']),
                        "ventas_completadas": resumen['ventas_completadas'],
                        "ventas_canceladas": resumen['ventas_canceladas']
                    }

                finally:
                    if cur:
                        cur.close()
                    if conn:
                        conn.close()
