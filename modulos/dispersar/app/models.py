from pydantic import BaseModel
from typing import Optional
from enum import Enum

class EstadoDispersion(str, Enum):
    PENDIENTE = "pendiente"
    REALIZADO = "realizado"
    FALLIDO = "fallido"

class DispersionCreate(BaseModel):
    beneficiario_id: int
    monto: float
    referencia_pago: Optional[str] = None

class Dispersion(DispersionCreate):
    id: int
    fecha_dispersion: str
    estado: EstadoDispersion

class DispersionUpdate(BaseModel):
    beneficiario_id: Optional[int] = None
    monto: Optional[float] = None
    estado: Optional[EstadoDispersion] = None
    referencia_pago: Optional[str] = None