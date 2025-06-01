from pydantic import BaseModel

class ProductoOut(BaseModel):
    id: int
    nombre: str
    cantidad: int
    precio: float

    class Config:
        orm_mode = True

class UsuarioOut(BaseModel):
    id: int
    nombre: str
    email: str
    rol: str

    class Config:
        orm_mode = True
