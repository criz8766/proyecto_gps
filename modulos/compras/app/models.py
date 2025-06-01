from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

class DetalleCompraCreate(BaseModel):
    producto_id: int
    nombre_producto: str
    cantidad: int
    precio_unitario: float
    subtotal: float

class DetalleCompra(DetalleCompraCreate):
    id: int
    compra_id: int

class CompraCreate(BaseModel):
    proveedor_id: int
    nombre_proveedor: str
    fecha_compra: str  # formato: YYYY-MM-DD
    numero_factura: str
    observaciones: Optional[str] = None
    detalles: List[DetalleCompraCreate]

class Compra(BaseModel):
    id: int
    proveedor_id: int
    nombre_proveedor: str
    fecha_compra: str
    numero_factura: str
    total: float
    observaciones: Optional[str] = None
    estado: str  # PENDIENTE, RECIBIDA, CANCELADA
    fecha_creacion: str
    detalles: List[DetalleCompra] = []

class NotaCreditoCreate(BaseModel):
    compra_id: int
    motivo: str
    monto: float
    observaciones: Optional[str] = None

class NotaCredito(NotaCreditoCreate):
    id: int
    numero_nota: str
    fecha_creacion: str
    estado: str  # PENDIENTE, APLICADA, CANCELADA

class ProveedorCreate(BaseModel):
    nombre: str
    rut: str
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None

class Proveedor(ProveedorCreate):
    id: int
    activo: bool = True