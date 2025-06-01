from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class TipoMovimiento(str, Enum):
    INGRESO = "INGRESO"
    EGRESO = "EGRESO"
    AJUSTE = "AJUSTE"
    TRANSFERENCIA = "TRANSFERENCIA"

class MetodoPrecio(str, Enum):
    ULTIMA_COMPRA = "ULTIMA_COMPRA"
    PRECIO_MEDIO_PONDERADO = "PRECIO_MEDIO_PONDERADO"
    FIFO = "FIFO"
    LIFO = "LIFO"
    LILO = "LILO"
    PERSONALIZADO = "PERSONALIZADO"

class EstadoProducto(str, Enum):
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"
    DESCONTINUADO = "DESCONTINUADO"

class ProductoCreate(BaseModel):
    codigo: str = Field(..., description="Código único del producto")
    nombre: str = Field(..., description="Nombre del producto")
    descripcion: Optional[str] = Field(None, description="Descripción detallada")
    categoria: str = Field(..., description="Categoría del producto")
    precio_venta: float = Field(..., ge=0, description="Precio de venta")
    metodo_precio: MetodoPrecio = Field(default=MetodoPrecio.ULTIMA_COMPRA)
    requiere_receta: bool = Field(default=False, description="Si requiere receta médica")
    es_psicotropico: bool = Field(default=False, description="Si es medicamento psicotrópico")
    stock_minimo: int = Field(default=0, ge=0, description="Stock mínimo para alertas")
    stock_maximo: Optional[int] = Field(None, ge=0, description="Stock máximo")
    estado: EstadoProducto = Field(default=EstadoProducto.ACTIVO)

class Producto(ProductoCreate):
    id: int
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime] = None

class BodegaCreate(BaseModel):
    nombre: str = Field(..., description="Nombre de la bodega")
    descripcion: Optional[str] = Field(None, description="Descripción de la bodega")
    ubicacion: Optional[str] = Field(None, description="Ubicación física")
    activa: bool = Field(default=True, description="Si la bodega está activa")

class Bodega(BodegaCreate):
    id: int
    fecha_creacion: datetime

class LoteCreate(BaseModel):
    numero_lote: str = Field(..., description="Número de lote")
    fecha_vencimiento: Optional[str] = Field(None, description="Fecha de vencimiento")
    precio_compra: float = Field(..., ge=0, description="Precio de compra del lote")
    cantidad_inicial: int = Field(..., ge=0, description="Cantidad inicial del lote")

class Lote(LoteCreate):
    id: int
    producto_id: int
    bodega_id: int
    cantidad_actual: int
    fecha_creacion: datetime

class StockCreate(BaseModel):
    producto_id: int = Field(..., description="ID del producto")
    bodega_id: int = Field(..., description="ID de la bodega")
    lote_id: Optional[int] = Field(None, description="ID del lote (opcional)")
    cantidad: int = Field(..., description="Cantidad en stock")
    precio_costo: float = Field(..., ge=0, description="Precio de costo unitario")

class Stock(StockCreate):
    id: int
    fecha_actualizacion: datetime

class MovimientoStockCreate(BaseModel):
    producto_id: int = Field(..., description="ID del producto")
    bodega_id: int = Field(..., description="ID de la bodega")
    lote_id: Optional[int] = Field(None, description="ID del lote")
    tipo_movimiento: TipoMovimiento = Field(..., description="Tipo de movimiento")
    cantidad: int = Field(..., description="Cantidad del movimiento")
    precio_unitario: float = Field(..., ge=0, description="Precio unitario")
    motivo: Optional[str] = Field(None, description="Motivo del movimiento")
    documento_referencia: Optional[str] = Field(None, description="Número de documento")

class MovimientoStock(MovimientoStockCreate):
    id: int
    fecha_movimiento: datetime
    usuario_id: Optional[str] = Field(None, description="ID del usuario que realizó el movimiento")

class AlertaStock(BaseModel):
    id: int
    producto_id: int
    bodega_id: int
    tipo_alerta: str = Field(..., description="Tipo de alerta (STOCK_MINIMO, VENCIMIENTO, etc.)")
    mensaje: str = Field(..., description="Mensaje de la alerta")
    fecha_alerta: datetime
    activa: bool = Field(default=True)

class InventarioRequest(BaseModel):
    bodega_id: Optional[int] = Field(None, description="ID de bodega específica (opcional)")
    tipo_inventario: str = Field(..., description="Tipo: GENERAL, SELECTIVO, BARRIDO")
    productos_seleccionados: Optional[list[int]] = Field(None, description="IDs de productos para inventario selectivo")

class ResumenStock(BaseModel):
    producto_id: int
    codigo_producto: str
    nombre_producto: str
    total_stock: int
    valor_total: float
    stock_por_bodega: list[dict]
    alertas_activas: int

class ProductoConStock(BaseModel):
    id: int
    codigo: str
    nombre: str
    descripcion: Optional[str]
    categoria: str
    precio_venta: float
    stock_total: int
    valor_inventario: float
    requiere_receta: bool
    es_psicotropico: bool
    stock_minimo: int
    tiene_alertas: bool
    estado: EstadoProducto