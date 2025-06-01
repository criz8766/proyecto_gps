from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

class DetalleVentaCreate(BaseModel):
    producto_id: int
    nombre_producto: str
    cantidad: int
    precio_unitario: float
    subtotal: float

class DetalleVenta(DetalleVentaCreate):
    id: int
    venta_id: int

class VentaCreate(BaseModel):
    paciente_id: int
    paciente_rut: str
    paciente_nombre: str
    tipo_venta: str  # "normal", "receta", "fraccionado"
    metodo_pago: str  # "efectivo", "tarjeta", "transferencia"
    descuento: Optional[float] = 0.0
    observaciones: Optional[str] = None
    detalles: List[DetalleVentaCreate]

class Venta(BaseModel):
    id: int
    paciente_id: int
    paciente_rut: str
    paciente_nombre: str
    fecha_venta: datetime
    tipo_venta: str
    metodo_pago: str
    subtotal: float
    descuento: float
    total: float
    estado: str  # "completada", "cancelada", "pendiente"
    observaciones: Optional[str]
    usuario_vendedor: str
    detalles: List[DetalleVenta]

class VentaResumen(BaseModel):
    id: int
    paciente_rut: str
    paciente_nombre: str
    fecha_venta: datetime
    total: float
    estado: str
    tipo_venta: str