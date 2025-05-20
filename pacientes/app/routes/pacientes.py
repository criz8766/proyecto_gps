from fastapi import APIRouter
from app.models import Paciente, PacienteCreate
from app.database import get_connection
from app.kafka_producer import enviar_evento

router = APIRouter()

@router.post("/", response_model=Paciente)
def crear_paciente(paciente: PacienteCreate):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO pacientes (nombre, rut, fecha_nacimiento) VALUES (%s, %s, %s) RETURNING id",
        (paciente.nombre, paciente.rut, paciente.fecha_nacimiento)
    )
    id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    evento = {
        "accion": "PACIENTE_CREADO",
        "paciente": paciente.dict()
    }
    enviar_evento("pacientes-events", evento)

    return Paciente(id=id, **paciente.dict())

