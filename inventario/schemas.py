from pydantic import BaseModel
import datetime

class ProductoBase(BaseModel):
    nombre_producto: str
    descripcion: str
    cantidad: int
    precio_unitario: float
    fecha_ingreso: datetime.date = datetime.date.today()

class ProductoCreate(ProductoBase):
    pass

class ProductoOut(ProductoBase):
    id: int

    class Config:
        orm_mode = True
