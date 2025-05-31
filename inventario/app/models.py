from pydantic import BaseModel
from typing import Optional

class InventarioCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    cantidad: int
    precio_unitario: float

class Inventario(InventarioCreate):
    id: int
