from sqlalchemy.orm import Session
from models import Producto
from schemas import ProductoCreate

def crear_producto(db: Session, producto: ProductoCreate):
    db_producto = Producto(**producto.dict())
    db.add(db_producto)
    db.commit()
    db.refresh(db_producto)
    return db_producto

def listar_productos(db: Session):
    return db.query(Producto).all()

def obtener_producto(db: Session, producto_id: int):
    return db.query(Producto).filter(Producto.id == producto_id).first()

def actualizar_producto(db: Session, producto_id: int, datos: ProductoCreate):
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if producto:
        for campo, valor in datos.dict().items():
            setattr(producto, campo, valor)
        db.commit()
        db.refresh(producto)
    return producto

def eliminar_producto(db: Session, producto_id: int):
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if producto:
        db.delete(producto)
        db.commit()
    return {"mensaje": "Producto eliminado"}
