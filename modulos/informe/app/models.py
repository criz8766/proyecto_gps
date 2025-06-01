from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, date

class FiltroFechas(BaseModel):
    fecha_inicio: date
    fecha_fin: date

class ReporteFacturasRequest(BaseModel):
    fecha_inicio: date
    fecha_fin: date

class ReporteFacturasResponse(BaseModel):
    total_facturas: int
    monto_total: float
    facturas: List[Dict[str, Any]]

class ReporteConsumosRequest(BaseModel):
    tipo: str  # "producto" o "beneficiario"
    filtro_id: Optional[str] = None  # ID del producto o beneficiario
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None

class ReporteConsumosResponse(BaseModel):
    tipo_reporte: str
    total_consumos: int
    detalle: List[Dict[str, Any]]

class ProductoSinMovimientoRequest(BaseModel):
    fecha_inicio: date
    fecha_fin: date

class ProductoSinMovimientoResponse(BaseModel):
    total_productos: int
    productos: List[Dict[str, Any]]

class ProductoMayorMovimientoResponse(BaseModel):
    productos: List[Dict[str, Any]]

class HistoricoVentasRequest(BaseModel):
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    producto_id: Optional[str] = None

class HistoricoVentasResponse(BaseModel):
    total_ventas: int
    monto_total: float
    ventas: List[Dict[str, Any]]

class ExportarRequest(BaseModel):
    tipo: str  # "facturas", "consumos", "ventas", "productos_sin_movimiento", "productos_mayor_movimiento"
    formato: str  # "excel"
    filtros: Optional[Dict[str, Any]] = None