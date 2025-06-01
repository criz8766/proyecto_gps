from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime
from enum import Enum


class EstadoFraccionamiento(str, Enum):
    ACTIVO = "activo"
    CANCELADO = "cancelado"
    FINALIZADO = "finalizado"


class FraccionamientoCreate(BaseModel):
    venta_id: int
    monto_total: float
    cuotas: int
    estado: EstadoFraccionamiento = EstadoFraccionamiento.ACTIVO
    fecha_inicio: str  # formato YYYY-MM-DD
    fecha_fin: str  # formato YYYY-MM-DD

    @validator('monto_total')
    def validar_monto_total(cls, v):
        if v <= 0:
            raise ValueError('El monto total debe ser mayor a 0')
        return v

    @validator('cuotas')
    def validar_cuotas(cls, v):
        if v <= 0:
            raise ValueError('El número de cuotas debe ser mayor a 0')
        return v

    @validator('fecha_fin')
    def validar_fecha_fin(cls, v, values):
        if 'fecha_inicio' in values:
            fecha_inicio = datetime.strptime(values['fecha_inicio'], '%Y-%m-%d')
            fecha_fin = datetime.strptime(v, '%Y-%m-%d')
            if fecha_fin <= fecha_inicio:
                raise ValueError('La fecha de fin debe ser posterior a la fecha de inicio')
        return v


class FraccionamientoUpdate(BaseModel):
    monto_total: Optional[float] = None
    cuotas: Optional[int] = None
    estado: Optional[EstadoFraccionamiento] = None
    fecha_inicio: Optional[str] = None
    fecha_fin: Optional[str] = None

    @validator('monto_total')
    def validar_monto_total(cls, v):
        if v is not None and v <= 0:
            raise ValueError('El monto total debe ser mayor a 0')
        return v

    @validator('cuotas')
    def validar_cuotas(cls, v):
        if v is not None and v <= 0:
            raise ValueError('El número de cuotas debe ser mayor a 0')
        return v


class Fraccionamiento(BaseModel):
    id: int
    venta_id: int
    monto_total: float
    cuotas: int
    monto_cuota: float
    estado: EstadoFraccionamiento
    fecha_inicio: str
    fecha_fin: str
    fecha_creacion: Optional[str] = None
    fecha_actualizacion: Optional[str] = None