from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal

# Modelos para Caja
class CajaCreate(BaseModel):
    usuario_id: int = Field(..., description="ID del usuario que abre la caja")
    saldo_inicial: Optional[Decimal] = Field(default=Decimal('0.00'), description="Saldo inicial de la caja")

class CajaClose(BaseModel):
    saldo_final: Decimal = Field(..., description="Saldo final al cerrar la caja")

class Caja(BaseModel):
    id: int
    usuario_id: int
    fecha_apertura: datetime
    fecha_cierre: Optional[datetime] = None
    saldo_inicial: Decimal
    saldo_final: Optional[Decimal] = None
    estado: str  # 'abierta' o 'cerrada'

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }

# Modelos para MovimientoCaja
class MovimientoCajaCreate(BaseModel):
    caja_id: int = Field(..., description="ID de la caja")
    tipo: str = Field(..., description="Tipo de movimiento: ingreso o egreso")
    monto: Decimal = Field(..., gt=0, description="Monto del movimiento (debe ser positivo)")
    descripcion: Optional[str] = Field(None, description="Descripción del movimiento")

    class Config:
        schema_extra = {
            "example": {
                "caja_id": 1,
                "tipo": "ingreso",
                "monto": 15000.50,
                "descripcion": "Venta de medicamentos"
            }
        }

class MovimientoCaja(BaseModel):
    id: int
    caja_id: int
    tipo: str
    monto: Decimal
    fecha: datetime
    descripcion: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }

# Modelo para respuesta con resumen de caja
class CajaResumen(BaseModel):
    caja: Caja
    total_ingresos: Decimal
    total_egresos: Decimal
    cantidad_movimientos: int

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }