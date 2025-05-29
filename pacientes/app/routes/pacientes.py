from fastapi import APIRouter, HTTPException, Response, Depends
from typing import List
from app.models import Paciente, PacienteCreate
from app.database import get_connection
from app.kafka_producer import enviar_evento
from app.security import validate_token # Importación para la protección de Auth0

router = APIRouter()

@router.post("/", response_model=Paciente, status_code=201)
def crear_paciente(paciente: PacienteCreate, current_user_payload: dict = Depends(validate_token)):
    # print(f"Usuario autenticado (payload en POST): {current_user_payload}")
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO pacientes (nombre, rut, fecha_nacimiento) VALUES (%s, %s, %s) RETURNING id",
            (paciente.nombre, paciente.rut, paciente.fecha_nacimiento)
        )
        id_nuevo_paciente = cur.fetchone()[0]
        conn.commit()

        try:
            datos_paciente_request = paciente.model_dump()
        except AttributeError:
            datos_paciente_request = paciente.dict()

        paciente_con_id = Paciente(id=id_nuevo_paciente, **datos_paciente_request)

        try:
            payload_kafka = paciente_con_id.model_dump()
        except AttributeError:
            payload_kafka = paciente_con_id.dict()

        evento_kafka = {
            "accion": "PACIENTE_CREADO",
            "paciente": payload_kafka
        }
        enviar_evento("pacientes-events", evento_kafka)
        return paciente_con_id
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@router.get("/{id_paciente}", response_model=Paciente)
def obtener_paciente_por_id(id_paciente: int, current_user_payload: dict = Depends(validate_token)):
    # print(f"Usuario autenticado (payload en GET por ID): {current_user_payload}")
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, nombre, rut, fecha_nacimiento FROM pacientes WHERE id = %s", (id_paciente,))
        paciente_db = cur.fetchone()

        if paciente_db is None:
            raise HTTPException(status_code=404, detail=f"Paciente con ID {id_paciente} no encontrado")

        return Paciente(
            id=paciente_db[0],
            nombre=paciente_db[1],
            rut=paciente_db[2],
            fecha_nacimiento=str(paciente_db[3])
        )
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@router.get("/rut/{rut_paciente}", response_model=Paciente)
def obtener_paciente_por_rut(rut_paciente: str, current_user_payload: dict = Depends(validate_token)):
    # print(f"Usuario autenticado (payload en GET por RUT): {current_user_payload}")
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, nombre, rut, fecha_nacimiento FROM pacientes WHERE rut = %s", (rut_paciente,))
        paciente_db = cur.fetchone()

        if paciente_db is None:
            raise HTTPException(status_code=404, detail=f"Paciente con RUT {rut_paciente} no encontrado")

        return Paciente(
            id=paciente_db[0],
            nombre=paciente_db[1],
            rut=paciente_db[2],
            fecha_nacimiento=str(paciente_db[3])
        )
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@router.get("/", response_model=List[Paciente])
def listar_pacientes(current_user_payload: dict = Depends(validate_token)):
    # print(f"Usuario autenticado (payload en GET todos): {current_user_payload}")
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, nombre, rut, fecha_nacimiento FROM pacientes ORDER BY nombre ASC")
        pacientes_db = cur.fetchall()
        pacientes_lista = []
        for paciente_tupla in pacientes_db:
            pacientes_lista.append(Paciente(
                id=paciente_tupla[0],
                nombre=paciente_tupla[1],
                rut=paciente_tupla[2],
                fecha_nacimiento=str(paciente_tupla[3])
            ))
        return pacientes_lista
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@router.put("/{id_paciente}", response_model=Paciente)
def actualizar_paciente(id_paciente: int, paciente_update_data: PacienteCreate, current_user_payload: dict = Depends(validate_token)):
    # print(f"Usuario autenticado (payload en PUT): {current_user_payload}")
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM pacientes WHERE id = %s", (id_paciente,))
        paciente_existente = cur.fetchone()

        if paciente_existente is None:
            raise HTTPException(status_code=404, detail=f"Paciente con ID {id_paciente} no encontrado para actualizar")

        cur.execute(
            """
            UPDATE pacientes 
            SET nombre = %s, rut = %s, fecha_nacimiento = %s 
            WHERE id = %s
            RETURNING id, nombre, rut, fecha_nacimiento
            """,
            (paciente_update_data.nombre, paciente_update_data.rut, paciente_update_data.fecha_nacimiento, id_paciente)
        )
        paciente_actualizado_db = cur.fetchone()
        conn.commit()

        if paciente_actualizado_db is None:
            raise HTTPException(status_code=500, detail="Error al actualizar el paciente")

        paciente_actualizado_obj = Paciente(
            id=paciente_actualizado_db[0],
            nombre=paciente_actualizado_db[1],
            rut=paciente_actualizado_db[2],
            fecha_nacimiento=str(paciente_actualizado_db[3])
        )

        try:
            payload_kafka = paciente_actualizado_obj.model_dump()
        except AttributeError:
            payload_kafka = paciente_actualizado_obj.dict()
        
        evento_kafka = {
            "accion": "PACIENTE_ACTUALIZADO",
            "paciente": payload_kafka
        }
        enviar_evento("pacientes-events", evento_kafka)
        return paciente_actualizado_obj
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@router.delete("/{id_paciente}", status_code=204)
def eliminar_paciente(id_paciente: int, current_user_payload: dict = Depends(validate_token)):
    # print(f"Usuario autenticado (payload en DELETE): {current_user_payload}")
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, nombre, rut, fecha_nacimiento FROM pacientes WHERE id = %s", (id_paciente,))
        paciente_existente_db = cur.fetchone()

        if paciente_existente_db is None:
            raise HTTPException(status_code=404, detail=f"Paciente con ID {id_paciente} no encontrado para eliminar")

        cur.execute("DELETE FROM pacientes WHERE id = %s RETURNING id", (id_paciente,))
        deleted_id = cur.fetchone()
        conn.commit()

        if deleted_id is None:
            raise HTTPException(status_code=500, detail="Error al intentar eliminar el paciente o ya no existía")

        paciente_eliminado_datos = {
            "id": paciente_existente_db[0],
            "nombre": paciente_existente_db[1],
            "rut": paciente_existente_db[2],
            "fecha_nacimiento": str(paciente_existente_db[3])
        }
        
        evento_kafka = {
            "accion": "PACIENTE_ELIMINADO",
            "paciente": paciente_eliminado_datos
        }
        enviar_evento("pacientes-events", evento_kafka)
        return Response(status_code=204)
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()