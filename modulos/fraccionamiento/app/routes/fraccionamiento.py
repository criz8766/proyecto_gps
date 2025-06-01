from fastapi import APIRouter, HTTPException, Response, Depends, Query
from typing import List, Optional
from app.models import Fraccionamiento, FraccionamientoCreate, FraccionamientoUpdate, EstadoFraccionamiento
from app.database import get_connection
from app.kafka_producer import enviar_evento
from app.security import validate_token, check_permission
import psycopg2

router = APIRouter()


def calcular_monto_cuota(monto_total: float, cuotas: int) -> float:
    """Calcula el monto por cuota"""
    return round(monto_total / cuotas, 2)


@router.get("/", response_model=List[Fraccionamiento])
def listar_fraccionamientos(
        estado: Optional[EstadoFraccionamiento] = Query(None, description="Filtrar por estado"),
        venta_id: Optional[int] = Query(None, description="Filtrar por ID de venta"),
        skip: int = Query(0, ge=0, description="Número de registros a omitir"),
        limit: int = Query(100, ge=1, le=1000, description="Número máximo de registros a retornar"),
        current_user_payload: dict = Depends(validate_token)
):
    """Listar fraccionamientos con filtros opcionales"""
    # Verificar permisos (puedes ajustar según los roles definidos)
    permissions = current_user_payload.get("permissions", [])
    if "read:fraccionamientos" not in permissions:
        raise HTTPException(status_code=403, detail="No tienes permisos para ver fraccionamientos")

    conn = get_connection()
    cur = conn.cursor()
    try:
        # Construir consulta con filtros
        query = """
                SELECT id, \
                       venta_id, \
                       monto_total, \
                       cuotas, \
                       monto_cuota, \
                       estado,
                       fecha_inicio, \
                       fecha_fin, \
                       fecha_creacion, \
                       fecha_actualizacion
                FROM fraccionamientos
                WHERE 1 = 1 \
                """
        params = []

        if estado:
            query += " AND estado = %s"
            params.append(estado.value)

        if venta_id:
            query += " AND venta_id = %s"
            params.append(venta_id)

        query += " ORDER BY fecha_creacion DESC LIMIT %s OFFSET %s"
        params.extend([limit, skip])

        cur.execute(query, params)
        fraccionamientos_db = cur.fetchall()

        fraccionamientos_lista = []
        for frac in fraccionamientos_db:
            fraccionamientos_lista.append(Fraccionamiento(
                id=frac[0],
                venta_id=frac[1],
                monto_total=float(frac[2]),
                cuotas=frac[3],
                monto_cuota=float(frac[4]),
                estado=EstadoFraccionamiento(frac[5]),
                fecha_inicio=str(frac[6]),
                fecha_fin=str(frac[7]),
                fecha_creacion=str(frac[8]) if frac[8] else None,
                fecha_actualizacion=str(frac[9]) if frac[9] else None
            ))

        return fraccionamientos_lista
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@router.post("/", response_model=Fraccionamiento, status_code=201)
def crear_fraccionamiento(
        fraccionamiento: FraccionamientoCreate,
        current_user_payload: dict = Depends(validate_token)
):
    """Crear un nuevo fraccionamiento"""
    # Verificar permisos
    permissions = current_user_payload.get("permissions", [])
    if "create:fraccionamientos" not in permissions:
        raise HTTPException(status_code=403, detail="No tienes permisos para crear fraccionamientos")

    conn = get_connection()
    cur = conn.cursor()
    try:
        # Calcular monto por cuota
        monto_cuota = calcular_monto_cuota(fraccionamiento.monto_total, fraccionamiento.cuotas)

        # Verificar si ya existe un fraccionamiento activo para esta venta
        cur.execute(
            "SELECT id FROM fraccionamientos WHERE venta_id = %s AND estado = 'activo'",
            (fraccionamiento.venta_id,)
        )
        fraccionamiento_existente = cur.fetchone()

        if fraccionamiento_existente:
            raise HTTPException(
                status_code=400,
                detail=f"Ya existe un fraccionamiento activo para la venta {fraccionamiento.venta_id}"
            )

        # Insertar nuevo fraccionamiento
        cur.execute(
            """
            INSERT INTO fraccionamientos
            (venta_id, monto_total, cuotas, monto_cuota, estado, fecha_inicio, fecha_fin, fecha_creacion)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW()) RETURNING id, fecha_creacion
            """,
            (
                fraccionamiento.venta_id,
                fraccionamiento.monto_total,
                fraccionamiento.cuotas,
                monto_cuota,
                fraccionamiento.estado.value,
                fraccionamiento.fecha_inicio,
                fraccionamiento.fecha_fin
            )
        )

        resultado = cur.fetchone()
        id_nuevo_fraccionamiento = resultado[0]
        fecha_creacion = resultado[1]
        conn.commit()

        # Crear objeto de respuesta
        fraccionamiento_creado = Fraccionamiento(
            id=id_nuevo_fraccionamiento,
            venta_id=fraccionamiento.venta_id,
            monto_total=fraccionamiento.monto_total,
            cuotas=fraccionamiento.cuotas,
            monto_cuota=monto_cuota,
            estado=fraccionamiento.estado,
            fecha_inicio=fraccionamiento.fecha_inicio,
            fecha_fin=fraccionamiento.fecha_fin,
            fecha_creacion=str(fecha_creacion)
        )

        # Enviar evento a Kafka
        try:
            payload_kafka = fraccionamiento_creado.model_dump()
        except AttributeError:
            payload_kafka = fraccionamiento_creado.dict()

        evento_kafka = {
            "accion": "FRACCIONAMIENTO_CREADO",
            "fraccionamiento": payload_kafka,
            "usuario": current_user_payload.get("sub", "unknown")
        }
        enviar_evento("fraccionamientos-events", evento_kafka)

        return fraccionamiento_creado

    except psycopg2.IntegrityError as e:
        conn.rollback()
        if "venta_id" in str(e):
            raise HTTPException(status_code=400, detail="La venta especificada no existe")
        raise HTTPException(status_code=400, detail="Error de integridad en los datos")
    except Exception as e:
        conn.rollback()
        raise
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@router.get("/{id_fraccionamiento}", response_model=Fraccionamiento)
def obtener_fraccionamiento_por_id(
        id_fraccionamiento: int,
        current_user_payload: dict = Depends(validate_token)
):
    """Obtener un fraccionamiento por su ID"""
    permissions = current_user_payload.get("permissions", [])
    if "read:fraccionamientos" not in permissions:
        raise HTTPException(status_code=403, detail="No tienes permisos para ver fraccionamientos")

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT id,
                   venta_id,
                   monto_total,
                   cuotas,
                   monto_cuota,
                   estado,
                   fecha_inicio,
                   fecha_fin,
                   fecha_creacion,
                   fecha_actualizacion
            FROM fraccionamientos
            WHERE id = %s
            """,
            (id_fraccionamiento,)
        )
        fraccionamiento_db = cur.fetchone()

        if fraccionamiento_db is None:
            raise HTTPException(
                status_code=404,
                detail=f"Fraccionamiento con ID {id_fraccionamiento} no encontrado"
            )

        return Fraccionamiento(
            id=fraccionamiento_db[0],
            venta_id=fraccionamiento_db[1],
            monto_total=float(fraccionamiento_db[2]),
            cuotas=fraccionamiento_db[3],
            monto_cuota=float(fraccionamiento_db[4]),
            estado=EstadoFraccionamiento(fraccionamiento_db[5]),
            fecha_inicio=str(fraccionamiento_db[6]),
            fecha_fin=str(fraccionamiento_db[7]),
            fecha_creacion=str(fraccionamiento_db[8]) if fraccionamiento_db[8] else None,
            fecha_actualizacion=str(fraccionamiento_db[9]) if fraccionamiento_db[9] else None
        )
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@router.put("/{id_fraccionamiento}", response_model=Fraccionamiento)
def actualizar_fraccionamiento(
        id_fraccionamiento: int,
        fraccionamiento_update: FraccionamientoUpdate,
        current_user_payload: dict = Depends(validate_token)
):
    """Actualizar un fraccionamiento existente"""
    permissions = current_user_payload.get("permissions", [])
    if "update:fraccionamientos" not in permissions:
        raise HTTPException(status_code=403, detail="No tienes permisos para actualizar fraccionamientos")

    conn = get_connection()
    cur = conn.cursor()
    try:
        # Verificar que existe el fraccionamiento
        cur.execute("SELECT * FROM fraccionamientos WHERE id = %s", (id_fraccionamiento,))
        fraccionamiento_existente = cur.fetchone()

        if fraccionamiento_existente is None:
            raise HTTPException(
                status_code=404,
                detail=f"Fraccionamiento con ID {id_fraccionamiento} no encontrado"
            )

        # Construir consulta de actualización dinámicamente
        campos_actualizar = []
        valores = []

        if fraccionamiento_update.monto_total is not None:
            campos_actualizar.append("monto_total = %s")
            valores.append(fraccionamiento_update.monto_total)

        if fraccionamiento_update.cuotas is not None:
            campos_actualizar.append("cuotas = %s")
            valores.append(fraccionamiento_update.cuotas)

        if fraccionamiento_update.estado is not None:
            campos_actualizar.append("estado = %s")
            valores.append(fraccionamiento_update.estado.value)

        if fraccionamiento_update.fecha_inicio is not None:
            campos_actualizar.append("fecha_inicio = %s")
            valores.append(fraccionamiento_update.fecha_inicio)

        if fraccionamiento_update.fecha_fin is not None:
            campos_actualizar.append("fecha_fin = %s")
            valores.append(fraccionamiento_update.fecha_fin)

        if not campos_actualizar:
            raise HTTPException(status_code=400, detail="No se proporcionaron campos para actualizar")

        # Recalcular monto_cuota si se actualiza monto_total o cuotas
        monto_total_nuevo = fraccionamiento_update.monto_total if fraccionamiento_update.monto_total is not None else \
        fraccionamiento_existente[2]
        cuotas_nuevas = fraccionamiento_update.cuotas if fraccionamiento_update.cuotas is not None else \
        fraccionamiento_existente[3]
        monto_cuota_nuevo = calcular_monto_cuota(monto_total_nuevo, cuotas_nuevas)

        # Agregar monto_cuota a la actualización
        campos_actualizar.append("monto_cuota = %s")
        valores.append(monto_cuota_nuevo)

        # Agregar fecha_actualizacion
        campos_actualizar.append("fecha_actualizacion = NOW()")

        # Construir la consulta final
        consulta_update = f"UPDATE fraccionamientos SET {', '.join(campos_actualizar)} WHERE id = %s"
        valores.append(id_fraccionamiento)

        cur.execute(consulta_update, tuple(valores))
        conn.commit()

        # Retornar el fraccionamiento actualizado
        cur.execute(
            """
            SELECT id,
                   venta_id,
                   monto_total,
                   cuotas,
                   monto_cuota,
                   estado,
                   fecha_inicio,
                   fecha_fin,
                   fecha_creacion,
                   fecha_actualizacion
            FROM fraccionamientos
            WHERE id = %s
            """,
            (id_fraccionamiento,)
        )
        fraccionamiento_db = cur.fetchone()

        fraccionamiento_actualizado = Fraccionamiento(
            id=fraccionamiento_db[0],
            venta_id=fraccionamiento_db[1],
            monto_total=float(fraccionamiento_db[2]),
            cuotas=fraccionamiento_db[3],
            monto_cuota=float(fraccionamiento_db[4]),
            estado=EstadoFraccionamiento(fraccionamiento_db[5]),
            fecha_inicio=str(fraccionamiento_db[6]),
            fecha_fin=str(fraccionamiento_db[7]),
            fecha_creacion=str(fraccionamiento_db[8]) if fraccionamiento_db[8] else None,
            fecha_actualizacion=str(fraccionamiento_db[9]) if fraccionamiento_db[9] else None
        )

        # Enviar evento a Kafka
        try:
            payload_kafka = fraccionamiento_actualizado.model_dump()
        except AttributeError:
            payload_kafka = fraccionamiento_actualizado.dict()

        evento_kafka = {
            "accion": "FRACCIONAMIENTO_ACTUALIZADO",
            "fraccionamiento": payload_kafka,
            "usuario": current_user_payload.get("sub", "unknown")
        }
        enviar_evento("fraccionamientos-events", evento_kafka)

        return fraccionamiento_actualizado

    except Exception:
        conn.rollback()
        raise
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
