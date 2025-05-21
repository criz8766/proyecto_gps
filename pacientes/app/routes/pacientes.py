from fastapi import APIRouter, HTTPException, Response # Response se usa para el código 204
from typing import List # Asegúrate de que List esté importado
from app.models import Paciente, PacienteCreate
from app.database import get_connection
from app.kafka_producer import enviar_evento
# Nota: json no se usa explícitamente aquí si kafka_producer ya maneja la serialización a JSON.

router = APIRouter()

@router.post("/", response_model=Paciente, status_code=201)
def crear_paciente(paciente: PacienteCreate):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO pacientes (nombre, rut, fecha_nacimiento) VALUES (%s, %s, %s) RETURNING id",
        (paciente.nombre, paciente.rut, paciente.fecha_nacimiento)
    )
    id_nuevo_paciente = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    # Crear la instancia completa del Paciente con el ID asignado
    # Usar model_dump() para Pydantic V2, o dict() para Pydantic V1
    try:
        datos_paciente_request = paciente.model_dump()
    except AttributeError: # Cae aquí si es Pydantic V1 y no tiene model_dump
        datos_paciente_request = paciente.dict()

    paciente_con_id = Paciente(id=id_nuevo_paciente, **datos_paciente_request)

    # Preparar el evento para Kafka usando el objeto Paciente que ya tiene el ID
    # Usar model_dump() para Pydantic V2, o dict() para Pydantic V1
    try:
        payload_kafka = paciente_con_id.model_dump()
    except AttributeError:
        payload_kafka = paciente_con_id.dict()

    evento_kafka = {
        "accion": "PACIENTE_CREADO",
        "paciente": payload_kafka
    }
    enviar_evento("pacientes-events", evento_kafka)

    # Retornar el objeto Paciente completo (con ID)
    return paciente_con_id

@router.get("/{id_paciente}", response_model=Paciente)
def obtener_paciente(id_paciente: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, nombre, rut, fecha_nacimiento FROM pacientes WHERE id = %s", (id_paciente,))
    paciente_db = cur.fetchone()
    cur.close()
    conn.close()

    if paciente_db is None:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    return Paciente(
        id=paciente_db[0],
        nombre=paciente_db[1],
        rut=paciente_db[2],
        fecha_nacimiento=str(paciente_db[3])
    )

@router.get("/", response_model=List[Paciente])
def listar_pacientes():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, nombre, rut, fecha_nacimiento FROM pacientes ORDER BY nombre ASC")
    pacientes_db = cur.fetchall()
    cur.close()
    conn.close()

    pacientes_lista = []
    for paciente_tupla in pacientes_db:
        pacientes_lista.append(Paciente(
            id=paciente_tupla[0],
            nombre=paciente_tupla[1],
            rut=paciente_tupla[2],
            fecha_nacimiento=str(paciente_tupla[3])
        ))
    
    return pacientes_lista

@router.put("/{id_paciente}", response_model=Paciente)
def actualizar_paciente(id_paciente: int, paciente_update_data: PacienteCreate):
    conn = get_connection()
    cur = conn.cursor()

    # Primero, verificar si el paciente existe
    cur.execute("SELECT id FROM pacientes WHERE id = %s", (id_paciente,))
    paciente_existente = cur.fetchone()

    if paciente_existente is None:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Paciente no encontrado para actualizar")

    # Si existe, proceder con la actualización
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
    cur.close()
    conn.close()

    if paciente_actualizado_db is None:
        # Esto no debería ocurrir si la verificación de existencia y el UPDATE fueron correctos
        raise HTTPException(status_code=500, detail="Error al actualizar el paciente")

    paciente_actualizado_obj = Paciente(
        id=paciente_actualizado_db[0],
        nombre=paciente_actualizado_db[1],
        rut=paciente_actualizado_db[2],
        fecha_nacimiento=str(paciente_actualizado_db[3])
    )

    # (Opcional) Enviar evento a Kafka
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

@router.delete("/{id_paciente}", status_code=204)
def eliminar_paciente(id_paciente: int):
    conn = get_connection()
    cur = conn.cursor()

    # Primero, verificar si el paciente existe para obtener sus datos antes de eliminar
    cur.execute("SELECT id, nombre, rut, fecha_nacimiento FROM pacientes WHERE id = %s", (id_paciente,))
    paciente_existente_db = cur.fetchone()

    if paciente_existente_db is None:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Paciente no encontrado para eliminar")

    # Si existe, proceder con la eliminación
    cur.execute("DELETE FROM pacientes WHERE id = %s RETURNING id", (id_paciente,)) # Usamos RETURNING para confirmar
    deleted_id = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    if deleted_id is None:
        # Esto podría ocurrir si hubo una condición de carrera y el paciente fue eliminado
        # por otro proceso entre la verificación y la eliminación, aunque es poco probable aquí.
        raise HTTPException(status_code=500, detail="Error al intentar eliminar el paciente o ya no existía")

    # (Opcional) Preparar datos del paciente eliminado para el evento Kafka
    # Necesitamos reconstruir un objeto o diccionario con los datos del paciente que fue eliminado
    # ya que la operación DELETE en sí misma no devuelve todos los campos, solo los que pongamos en RETURNING.
    # Ya los obtuvimos con paciente_existente_db.
    paciente_eliminado_datos = {
        "id": paciente_existente_db[0],
        "nombre": paciente_existente_db[1],
        "rut": paciente_existente_db[2],
        "fecha_nacimiento": str(paciente_existente_db[3])
    }

    evento_kafka = {
        "accion": "PACIENTE_ELIMINADO",
        "paciente": paciente_eliminado_datos # Enviamos los datos del paciente que fue eliminado
    }
    enviar_evento("pacientes-events", evento_kafka)

    # Para un DELETE exitoso, es común devolver un status_code 204 No Content.
    # En este caso, FastAPI no enviará un cuerpo de respuesta.
    # Si quisieras devolver un mensaje JSON, cambiarías el status_code (ej. 200)
    # y harías `return {"mensaje": "Paciente eliminado exitosamente"}`
    return Response(status_code=204)

@router.get("/rut/{rut_paciente}", response_model=Paciente)
def obtener_paciente_por_rut(rut_paciente: str):
    conn = get_connection()
    cur = conn.cursor()
    # Buscamos por el campo 'rut' que debe ser único en tu tabla
    cur.execute("SELECT id, nombre, rut, fecha_nacimiento FROM pacientes WHERE rut = %s", (rut_paciente,))
    paciente_db = cur.fetchone() # fetchone() recupera una sola fila o None
    cur.close()
    conn.close()

    if paciente_db is None:
        # Si no se encontró el paciente, devolvemos un error 404
        raise HTTPException(status_code=404, detail=f"Paciente con RUT {rut_paciente} no encontrado")

    # Si se encontró, mapeamos los datos de la tupla paciente_db a un objeto Paciente
    return Paciente(
        id=paciente_db[0],
        nombre=paciente_db[1],
        rut=paciente_db[2],
        fecha_nacimiento=str(paciente_db[3]) # Convertimos la fecha a string
    )