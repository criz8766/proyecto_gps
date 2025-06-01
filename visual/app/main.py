from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database import Base, engine, SessionLocal
from models import Producto  # Puedes agregar modelos de ventas, compras, usuarios también
from visual import ProductoOut
from security import require_permission

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Módulos Visuales")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#  Módulo de stock
@app.get("/modulo/stock", response_model=list[ProductoOut], dependencies=[Depends(require_permission("ver:stock"))])
def ver_stock(db: Session = Depends(get_db)):
    return db.query(Producto).all()

#  Módulo de ventas
@app.get("/modulo/ventas", dependencies=[Depends(require_permission("ver:ventas"))])
def ver_ventas():
    return {"modulo": "ventas", "mensaje": "Visualización de ventas autorizada"}

#  Módulo de compras
@app.get("/modulo/compras", dependencies=[Depends(require_permission("ver:compras"))])
def ver_compras():
    return {"modulo": "compras", "mensaje": "Visualización de compras autorizada"}

#  Módulo de usuarios
@app.get("/modulo/usuarios", dependencies=[Depends(require_permission("ver:usuarios"))])
def ver_usuarios():
    return {"modulo": "usuarios", "mensaje": "Lista de usuarios (autorizado)"}

#  Módulo de informes
@app.get("/modulo/informes", dependencies=[Depends(require_permission("ver:informes"))])
def ver_informes():
    return {"modulo": "informes", "mensaje": "Informes accesibles con permisos"}
