from fastapi import APIRouter, HTTPException, Response, Depends
from typing import List
from app.models import Beneficiario, BeneficiarioCreate, BeneficiarioUpdate
from app.database import get_connection
from app.kafka_producer import enviar_evento
from app.security import validate_token

router = APIRouter()


@router.post("/", response_model=Beneficiario, status_code=201)
def crear_beneficiario(beneficiario: BeneficiarioCreate, current_user_payload: dict = Depends(validate_token)):
    """Crear un nuevo beneficiario"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Verificar si ya existe un beneficiario con el mismo RUT
        cur.execute("SELECT id FROM beneficiarios WHERE rut = %s", (beneficiario.rut,))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail=f"Ya existe un beneficiario con RUT {beneficiario.rut}")

        # Insertar nuevo beneficiario
        cur.execute(
            """INSERT INTO beneficiarios (rut, nombre, apellido_paterno, apellido_materno,
                                          fecha_nacimiento, telefono, email, direccion, comuna, region, estado)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
            (beneficiario.rut, beneficiario.nombre, beneficiario.apellido_paterno,
             beneficiario.apellido_materno, beneficiario.fecha_nacimiento,
             beneficiario.telefono, beneficiario.email, beneficiario.direccion,
             beneficiario.comuna, beneficiario.region, beneficiario.estado)
        )
        id_nuevo_beneficiario = cur.fetchone()[0]
        conn.commit()

        # Crear objeto beneficiario con ID
        try:
            datos_beneficiario_request = beneficiario.model_dump()
        except AttributeError:
            datos_beneficiario_request = beneficiario.dict()

        beneficiario_con_id = Beneficiario(id=id_nuevo_beneficiario, **datos_beneficiario_request)

        # Enviar evento a Kafka
        try:
            payload_kafka = beneficiario_con_id.model_dump()
        except AttributeError:
            payload_kafka = beneficiario_con_id.dict()

        evento_kafka = {
            "accion": "BENEFICIARIO_CREADO",
            "beneficiario": payload_kafka
        }
        enviar_evento("beneficiarios-events", evento_kafka)

        return beneficiario_con_id
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@router.get("/{id_beneficiario}", response_model=Beneficiario)
def obtener_beneficiario_por_id(id_beneficiario: int, current_user_payload: dict = Depends(validate_token)):
    """Obtener beneficiario por ID"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """SELECT id,
                      rut,
                      nombre,
                      apellido_paterno,
                      apellido_materno,
                      fecha_nacimiento,
                      telefono,
                      email,
                      direccion,
                      comuna,
                      region,
                      estado,
                      fecha_registro
               FROM beneficiarios
               WHERE id = %s""",
            (id_beneficiario,)
        )
        beneficiario_db = cur.fetchone()

        if beneficiario_db is None:
            raise HTTPException(status_code=404, detail=f"Beneficiario con ID {id_beneficiario} no encontrado")

        return Beneficiario(
            id=beneficiario_db[0],
            rut=beneficiario_db[1],
            nombre=beneficiario_db[2],
            apellido_paterno=beneficiario_db[3],
            apellido_materno=beneficiario_db[4],
            fecha_nacimiento=str(beneficiario_db[5]),
            telefono=beneficiario_db[6],
            email=beneficiario_db[7],
            direccion=beneficiario_db[8],
            comuna=beneficiario_db[9],
            region=beneficiario_db[10],
            estado=beneficiario_db[11],
            fecha_registro=str(beneficiario_db[12])
        )
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@router.get("/rut/{rut_beneficiario}", response_model=Beneficiario)
def obtener_beneficiario_por_rut(rut_beneficiario: str, current_user_payload: dict = Depends(validate_token)):
    """Obtener beneficiario por RUT"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """SELECT id,
                      rut,
                      nombre,
                      apellido_paterno,
                      apellido_materno,
                      fecha_nacimiento,
                      telefono,
                      email,
                      direccion,
                      comuna,
                      region,
                      estado,
                      fecha_registro
               FROM beneficiarios
               WHERE rut = %s""",
            (rut_beneficiario,)
        )
        beneficiario_db = cur.fetchone()

        if beneficiario_db is None:
            raise HTTPException(status_code=404, detail=f"Beneficiario con RUT {rut_beneficiario} no encontrado")

        return Beneficiario(
            id=beneficiario_db[0],
            rut=beneficiario_db[1],
            nombre=beneficiario_db[2],
            apellido_paterno=beneficiario_db[3],
            apellido_materno=beneficiario_db[4],
            fecha_nacimiento=str(beneficiario_db[5]),
            telefono=beneficiario_db[6],
            email=beneficiario_db[7],
            direccion=beneficiario_db[8],
            comuna=beneficiario_db[9],
            region=beneficiario_db[10],
            estado=beneficiario_db[11],
            fecha_registro=str(beneficiario_db[12])
        )
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@router.get("/", response_model=List[Beneficiario])
def listar_beneficiarios(skip: int = 0, limit: int = 100, current_user_payload: dict = Depends(validate_token)):
    """Listar todos los beneficiarios con paginación"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """SELECT id,
                      rut,
                      nombre,
                      apellido_paterno,
                      apellido_materno,
                      fecha_nacimiento,
                      telefono,
                      email,
                      direccion,
                      comuna,
                      region,
                      estado,
                      fecha_registro
               FROM beneficiarios
               ORDER BY apellido_paterno, apellido_materno, nombre
                   LIMIT %s
               OFFSET %s""",
            (limit, skip)
        )
        beneficiarios_db = cur.fetchall()
        beneficiarios_lista = []

        for beneficiario_tupla in beneficiarios_db:
            beneficiarios_lista.append(Beneficiario(
                id=beneficiario_tupla[0],
                rut=beneficiario_tupla[1],
                nombre=beneficiario_tupla[2],
                apellido_paterno=beneficiario_tupla[3],
                apellido_materno=beneficiario_tupla[4],
                fecha_nacimiento=str(beneficiario_tupla[5]),
                telefono=beneficiario_tupla[6],
                email=beneficiario_tupla[7],
                direccion=beneficiario_tupla[8],
                comuna=beneficiario_tupla[9],
                region=beneficiario_tupla[10],
                estado=beneficiario_tupla[11],
                fecha_registro=str(beneficiario_tupla[12])
            ))
        return beneficiarios_lista
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@router.put("/{id_beneficiario}", response_model=Beneficiario)
def actualizar_beneficiario(id_beneficiario: int, beneficiario_update: BeneficiarioUpdate,
                            current_user_payload: dict = Depends(validate_token)):
    """Actualizar datos de un beneficiario"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Verificar que el beneficiario existe
        cur.execute("SELECT id FROM beneficiarios WHERE id = %s", (id_beneficiario,))
        if cur.fetchone() is None:
            raise HTTPException(status_code=404, detail=f"Beneficiario con ID {id_beneficiario} no encontrado")

        # Verificar si el RUT ya existe en otro beneficiario
        if beneficiario_update.rut:
            cur.execute("SELECT id FROM beneficiarios WHERE rut = %s AND id != %s",
                        (beneficiario_update.rut, id_beneficiario))
            if cur.fetchone():
                raise HTTPException(status_code=400,
                                    detail=f"Ya existe otro beneficiario con RUT {beneficiario_update.rut}")

        # Construir la consulta de actualización dinámicamente
        campos_actualizar = []
        valores = []

        if beneficiario_update.rut is not None:
            campos_actualizar.append("rut = %s")
            valores.append(beneficiario_update.rut)
        if beneficiario_update.nombre is not None:
            campos_actualizar.append("nombre = %s")
            valores.append(beneficiario_update.nombre)
        if beneficiario_update.apellido_paterno is not None:
            campos_actualizar.append("apellido_paterno = %s")
            valores.append(beneficiario_update.apellido_paterno)
        if beneficiario_update.apellido_materno is not None:
            campos_actualizar.append("apellido_materno = %s")
            valores.append(beneficiario_update.apellido_materno)
        if beneficiario_update.fecha_nacimiento is not None:
            campos_actualizar.append("fecha_nacimiento = %s")
            valores.append(beneficiario_update.fecha_nacimiento)
        if beneficiario_update.telefono is not None:
            campos_actualizar.append("telefono = %s")
            valores.append(beneficiario_update.telefono)
        if beneficiario_update.email is not None:
            campos_actualizar.append("email = %s")
            valores.append(beneficiario_update.email)
        if beneficiario_update.direccion is not None:
            campos_actualizar.append("direccion = %s")
            valores.append(beneficiario_update.direccion)
        if beneficiario_update.comuna is not None:
            campos_actualizar.append("comuna = %s")
            valores.append(beneficiario_update.comuna)
        if beneficiario_update.region is not None:
            campos_actualizar.append("region = %s")
            valores.append(beneficiario_update.region)
        if beneficiario_update.estado is not None:
            campos_actualizar.append("estado = %s")
            valores.append(beneficiario_update.estado)

        if not campos_actualizar:
            raise HTTPException(status_code=400, detail="No se proporcionaron campos para actualizar")

        valores.append(id_beneficiario)

        consulta_update = f"""
            UPDATE beneficiarios 
            SET {', '.join(campos_actualizar)}
            WHERE id = %s
            RETURNING id, rut, nombre, apellido_paterno, apellido_materno, fecha_nacimiento, 
                     telefono, email, direccion, comuna, region, estado, fecha_registro
        """

        cur.execute(consulta_update, valores)
        beneficiario_actualizado_db = cur.fetchone()
        conn.commit()

        if beneficiario_actualizado_db is None:
            raise HTTPException(status_code=500, detail="Error al actualizar el beneficiario")

        beneficiario_actualizado_obj = Beneficiario(
            id=beneficiario_actualizado_db[0],
            rut=beneficiario_actualizado_db[1],
            nombre=beneficiario_actualizado_db[2],
            apellido_paterno=beneficiario_actualizado_db[3],
            apellido_materno=beneficiario_actualizado_db[4],
            fecha_nacimiento=str(beneficiario_actualizado_db[5]),
            telefono=beneficiario_actualizado_db[6],
            email=beneficiario_actualizado_db[7],
            direccion=beneficiario_actualizado_db[8],
            comuna=beneficiario_actualizado_db[9],
            region=beneficiario_actualizado_db[10],
            estado=beneficiario_actualizado_db[11],
            fecha_registro=str(beneficiario_actualizado_db[12])
        )

        # Enviar evento a Kafka
        try:
            payload_kafka = beneficiario_actualizado_obj.model_dump()
        except AttributeError:
            payload_kafka = beneficiario_actualizado_obj.dict()

        evento_kafka = {
            "accion": "BENEFICIARIO_ACTUALIZADO",
            "beneficiario": payload_kafka
        }
        enviar_evento("beneficiarios-events", evento_kafka)

        return beneficiario_actualizado_obj
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@router.delete("/{id_beneficiario}", status_code=204)
def eliminar_beneficiario(id_beneficiario: int, current_user_payload: dict = Depends(validate_token)):
    """Eliminar un beneficiario (cambiar estado a inactivo)"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Verificar que el beneficiario existe
        cur.execute(
            """SELECT id,
                      rut,
                      nombre,
                      apellido_paterno,
                      apellido_materno,
                      fecha_nacimiento,
                      telefono,
                      email,
                      direccion,
                      comuna,
                      region,
                      estado,
                      fecha_registro
               FROM beneficiarios
               WHERE id = %s""",
            (id_beneficiario,)
        )
        beneficiario_existente_db = cur.fetchone()

        if beneficiario_existente_db is None:
            raise HTTPException(status_code=404, detail=f"Beneficiario con ID {id_beneficiario} no encontrado")

        # En lugar de eliminar físicamente, cambiar estado a 'inactivo'
        cur.execute(
            "UPDATE beneficiarios SET estado = 'inactivo' WHERE id = %s RETURNING id",
            (id_beneficiario,)
        )
        updated_id = cur.fetchone()
        conn.commit()

        if updated_id is None:
            raise HTTPException(status_code=500, detail="Error al desactivar el beneficiario")

        # Preparar datos del beneficiario eliminado para el evento
        beneficiario_eliminado_datos = {
            "id": beneficiario_existente_db[0],
            "rut": beneficiario_existente_db[1],
            "nombre": beneficiario_existente_db[2],
            "apellido_paterno": beneficiario_existente_db[3],
            "apellido_materno": beneficiario_existente_db[4],
            "fecha_nacimiento": str(beneficiario_existente_db[5]),
            "telefono": beneficiario_existente_db[6],
            "email": beneficiario_existente_db[7],
            "direccion": beneficiario_existente_db[8],
            "comuna": beneficiario_existente_db[9],
            "region": beneficiario_existente_db[10],
            "estado": "inactivo",
            "fecha_registro": str(beneficiario_existente_db[12])
        }

        # Enviar evento a Kafka
        evento_kafka = {
            "accion": "BENEFICIARIO_ELIMINADO",
            "beneficiario": beneficiario_eliminado_datos
        }
        enviar_evento("beneficiarios-events", evento_kafka)

        return Response(status_code=204)
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@router.get("/buscar/", response_model=List[Beneficiario])
def buscar_beneficiarios(
        nombre: str = None,
        rut: str = None,
        comuna: str = None,
        estado: str = "activo",
        current_user_payload: dict = Depends(validate_token)
):
    """Buscar beneficiarios por diferentes criterios"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        condiciones = ["estado = %s"]
        valores = [estado]

        if nombre:
            condiciones.append("(nombre ILIKE %s OR apellido_paterno ILIKE %s OR apellido_materno ILIKE %s)")
            patron_nombre = f"%{nombre}%"
            valores.extend([patron_nombre, patron_nombre, patron_nombre])

        if rut:
            condiciones.append("rut ILIKE %s")
            valores.append(f"%{rut}%")

        if comuna:
            condiciones.append("comuna ILIKE %s")
            valores.append(f"%{comuna}%")

        consulta = f"""
            SELECT id, rut, nombre, apellido_paterno, apellido_materno, fecha_nacimiento, 
                   telefono, email, direccion, comuna, region, estado, fecha_registro 
            FROM beneficiarios 
            WHERE {' AND '.join(condiciones)}
            ORDER BY apellido_paterno, apellido_materno, nombre
            LIMIT 50
        """

        cur.execute(consulta, valores)
        beneficiarios_db = cur.fetchall()
        beneficiarios_lista = []

        for beneficiario_tupla in beneficiarios_db:
            beneficiarios_lista.append(Beneficiario(
                id=beneficiario_tupla[0],
                rut=beneficiario_tupla[1],
                nombre=beneficiario_tupla[2],
                apellido_paterno=beneficiario_tupla[3],
                apellido_materno=beneficiario_tupla[4],
                fecha_nacimiento=str(beneficiario_tupla[5]),
                telefono=beneficiario_tupla[6],
                email=beneficiario_tupla[7],
                direccion=beneficiario_tupla[8],
                comuna=beneficiario_tupla[9],
                region=beneficiario_tupla[10],
                estado=beneficiario_tupla[11],
                fecha_registro=str(beneficiario_tupla[12])
            ))

        return beneficiarios_lista
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()