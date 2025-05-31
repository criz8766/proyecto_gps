# inventario.py
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from database import engine, SessionLocal
from models import Base, Producto
from schemas import ProductoCreate, ProductoOut
import crud

# Crear tablas
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Microservicio de Inventario")

# Dependencia para obtener DB

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpoints CRUD
@app.post("/inventario/", response_model=ProductoOut)
def crear_producto(producto: ProductoCreate, db: Session = Depends(get_db)):
    return crud.crear_producto(db, producto)

@app.get("/inventario/", response_model=list[ProductoOut])
def listar_productos(db: Session = Depends(get_db)):
    return crud.listar_productos(db)

@app.get("/inventario/{producto_id}", response_model=ProductoOut)
def obtener_producto(producto_id: int, db: Session = Depends(get_db)):
    return crud.obtener_producto(db, producto_id)

@app.put("/inventario/{producto_id}", response_model=ProductoOut)
def actualizar_producto(producto_id: int, datos: ProductoCreate, db: Session = Depends(get_db)):
    return crud.actualizar_producto(db, producto_id, datos)

@app.delete("/inventario/{producto_id}")
def eliminar_producto(producto_id: int, db: Session = Depends(get_db)):
    return crud.eliminar_producto(db, producto_id)
