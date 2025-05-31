from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

import models, schemas, crud
from database import SessionLocal, engine
from auth import get_current_user  # <- auth0 token validator

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS (ajusta los orígenes permitidos para tu frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # cambia esto en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependencia de base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpoints CRUD protegidos por token válido de Auth0

@app.post("/inventario/", response_model=schemas.Producto, dependencies=[Depends(get_current_user)])
def crear_producto(producto: schemas.ProductoCreate, db: Session = Depends(get_db)):
    return crud.crear_producto(db=db, producto=producto)

@app.get("/inventario/", response_model=List[schemas.Producto], dependencies=[Depends(get_current_user)])
def listar_productos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.obtener_productos(db, skip=skip, limit=limit)

@app.get("/inventario/{producto_id}", response_model=schemas.Producto, dependencies=[Depends(get_current_user)])
def obtener_producto(producto_id: int, db: Session = Depends(get_db)):
    db_producto = crud.obtener_producto(db, producto_id=producto_id)
    if db_producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return db_producto

@app.put("/inventario/{producto_id}", response_model=schemas.Producto, dependencies=[Depends(get_current_user)])
def actualizar_producto(producto_id: int, producto: schemas.ProductoCreate, db: Session = Depends(get_db)):
    return crud.actualizar_producto(db, producto_id, producto)

@app.delete("/inventario/{producto_id}", dependencies=[Depends(get_current_user)])
def eliminar_producto(producto_id: int, db: Session = Depends(get_db)):
    return crud.eliminar_producto(db, producto_id)
