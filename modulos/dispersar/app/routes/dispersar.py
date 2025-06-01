from fastapi import APIRouter, HTTPException, Response, Depends
from typing import List
from datetime import datetime
from app.models import Dispersion, DispersionCreate, DispersionUpdate, EstadoDispersion
from app.database import get_connection
from app.kafka_producer import enviar_evento
from app.security import validate_token

router = APIRouter()


@router.post("/", response_model=Dispersion, status_code=201)
def crear_dispersion(dispersion: DispersionCreate, current_user_payload: dict = Depends(validate_token)):
    """Crear una nueva dispersión de pago"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Insertar nueva dispersión con estado pendiente por defecto
        cur.execute(
            """
            INSERT INTO dispersiones (beneficiario_id, monto, fecha_dispersion, estado, referencia_pago)
            VALUES (%s, %s, %s, %s, %s) RETURNING id
            """,
            (
                dispersion.beneficiario_id,
                dispersion.monto,
                datetime.now().isoformat(),
                EstadoDispersion.PENDIENTE.value,
                dispersion.referencia_pago
            )
        )
        id_nueva_dispersion = cur.fetchone()[0]
        conn.commit()

        # Obtener la dispersión creada
        cur.execute(
            "SELECT id, beneficiario_id, monto, fecha_dispersion, estado, referencia_pago FROM dispersiones WHERE id = %s",
            (id_nueva_dispersion,)
        )
        dispersion_db = cur.fetchone()

        dispersion_creada = Dispersion(
            id=dispersion_db[0],
            beneficiario_id=dispersion_db[1],
            monto=dispersion_db[2],
            fecha_dispersion=str(dispersion_db[3]),
            estado=dispersion_db[4],
            referencia_pago=dispersion_db[5]
        )

        # Enviar evento a Kafka
        try:
            payload_kafka = dispersion_creada.model_dump()
        except AttributeError:
            payload_kafka = dispersion_creada.dict()

        evento_kafka = {
            "accion": "DISPERSION_CREADA",
            "dispersion": payload_kafka
        }
        enviar_evento("dispersiones-events", evento_kafka)

        return dispersion_creada
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@router.get("/{id_dispersion}", response_model=Dispersion)
def obtener_dispersion_por_id(id_dispersion: int, current_user_payload: dict = Depends(validate_token)):
    """Obtener una dispersión por ID"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT id, beneficiario_id, monto, fecha_dispersion, estado, referencia_pago FROM dispersiones WHERE id = %s",
            (id_dispersion,)
        )
        dispersion_db = cur.fetchone()

        if dispersion_db is None:
            raise HTTPException(status_code=404, detail=f"Dispersión con ID {id_dispersion} no encontrada")

        return Dispersion(
            id=dispersion_db[0],
            beneficiario_id=dispersion_db[1],
            monto=dispersion_db[2],
            fecha_dispersion=str(dispersion_db[3]),
            estado=dispersion_db[4],
            referencia_pago=dispersion_db[5]
        )
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@router.get("/", response_model=List[Dispersion])
def listar_dispersiones(current_user_payload: dict = Depends(validate_token)):
    """Listar todas las dispersiones"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT id, beneficiario_id, monto, fecha_dispersion, estado, referencia_pago FROM dispersiones ORDER BY fecha_dispersion DESC"
        )
        dispersiones_db = cur.fetchall()
        dispersiones_lista = []

        for dispersion_tupla in dispersiones_db:
            dispersiones_lista.append(Dispersion(
                id=dispersion_tupla[0],
                beneficiario_id=dispersion_tupla[1],
                monto=dispersion_tupla[2],
                fecha_dispersion=str(dispersion_tupla[3]),
                estado=dispersion_tupla[4],
                referencia_pago=dispersion_tupla[5]
            ))
        return dispersiones_lista
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@router.put("/{id_dispersion}", response_model=Dispersion)
def actualizar_dispersion(
        id_dispersion: int,
        dispersion_update: DispersionUpdate,
        current_user_payload: dict = Depends(validate_token)
):
    """Actualizar una dispersión existente"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Verificar que la dispersión existe
        cur.execute("SELECT id FROM dispersiones WHERE id = %s", (id_dispersion,))
        dispersion_existente = cur.fetchone()

        if dispersion_existente is None:
            raise HTTPException(status_code=404, detail=f"Dispersión con ID {id_dispersion} no encontrada")

        # Construir query dinámico para actualizar solo los campos proporcionados
        campos_actualizar = []
        valores = []

        if dispersion_update.beneficiario_id is not None:
            campos_actualizar.append("beneficiario_id = %s")
            valores.append(dispersion_update.beneficiario_id)

        if dispersion_update.monto is not None:
            campos_actualizar.append("monto = %s")
            valores.append(dispersion_update.monto)

        if dispersion_update.estado is not None:
            campos_actualizar.append("estado = %s")
            valores.append(dispersion_update.estado.value)

        if dispersion_update.referencia_pago is not None:
            campos_actualizar.append("referencia_pago = %s")
            valores.append(dispersion_update.referencia_pago)

        if not campos_actualizar:
            raise HTTPException(status_code=400, detail="No se proporcionaron campos para actualizar")

        valores.append(id_dispersion)
        query = f"UPDATE dispersiones SET {', '.join(campos_actualizar)} WHERE id = %s RETURNING id, beneficiario_id, monto, fecha_dispersion, estado, referencia_pago"

        cur.execute(query, valores)
        dispersion_actualizada_db = cur.fetchone()
        conn.commit()

        if dispersion_actualizada_db is None:
            raise HTTPException(status_code=500, detail="Error al actualizar la dispersión")

        dispersion_actualizada = Dispersion(
            id=dispersion_actualizada_db[0],
            beneficiario_id=dispersion_actualizada_db[1],
            monto=dispersion_actualizada_db[2],
            fecha_dispersion=str(dispersion_actualizada_db[3]),
            estado=dispersion_actualizada_db[4],
            referencia_pago=dispersion_actualizada_db[5]
        )

        # Enviar evento a Kafka
        try:
            payload_kafka = dispersion_actualizada.model_dump()
        except AttributeError:
            payload_kafka = dispersion_actualizada.dict()

        evento_kafka = {
            "accion": "DISPERSION_ACTUALIZADA",
            "dispersion": payload_kafka
        }
        enviar_evento("dispersiones-events", evento_kafka)

        return dispersion_actualizada
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@router.delete("/{id_dispersion}", status_code=204)
def eliminar_dispersion(id_dispersion: int, current_user_payload: dict = Depends(validate_token)):
    """Eliminar una dispersión"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Obtener datos de la dispersión antes de eliminar
        cur.execute(
            "SELECT id, beneficiario_id, monto, fecha_dispersion, estado, referencia_pago FROM dispersiones WHERE id = %s",
            (id_dispersion,)
        )
        dispersion_existente_db = cur.fetchone()

        if dispersion_existente_db is None:
            raise HTTPException(status_code=404, detail=f"Dispersión con ID {id_dispersion} no encontrada")

        # Eliminar la dispersión
        cur.execute("DELETE FROM dispersiones WHERE id = %s RETURNING id", (id_dispersion,))
        deleted_id = cur.fetchone()
        conn.commit()

        if deleted_id is None:
            raise HTTPException(status_code=500, detail="Error al eliminar la dispersión")

        # Preparar datos para evento Kafka
        dispersion_eliminada_datos = {
            "id": dispersion_existente_db[0],
            "beneficiario_id": dispersion_existente_db[1],
            "monto": dispersion_existente_db[2],
            "fecha_dispersion": str(dispersion_existente_db[3]),
            "estado": dispersion_existente_db[4],
            "referencia_pago": dispersion_existente_db[5]
        }

        evento_kafka = {
            "accion": "DISPERSION_ELIMINADA",
            "dispersion": dispersion_eliminada_datos
        }
        enviar_evento("dispersiones-events", evento_kafka)

        return Response(status_code=204)
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@router.get("/beneficiario/{beneficiario_id}", response_model=List[Dispersion])
def obtener_dispersiones_por_beneficiario(beneficiario_id: int, current_user_payload: dict = Depends(validate_token)):
    """Obtener todas las dispersiones de un beneficiario específico"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT id, beneficiario_id, monto, fecha_dispersion, estado, referencia_pago
            FROM dispersiones
            WHERE beneficiario_id = %s
            ORDER BY fecha_dispersion DESC
            """,
            (beneficiario_id,)
        )
        dispersiones_db = cur.fetchall()
        dispersiones_lista = []

        for dispersion_tupla in dispersiones_db:
            dispersiones_lista.append(Dispersion(
                id=dispersion_tupla[0],
                beneficiario_id=dispersion_tupla[1],
                monto=dispersion_tupla[2],
                fecha_dispersion=str(dispersion_tupla[3]),
                estado=dispersion_tupla[4],
                referencia_pago=dispersion_tupla[5]
            ))
        return dispersiones_lista
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()