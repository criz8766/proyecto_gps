from sqlalchemy import Column, Integer, String, Float, Date
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class Producto(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True)
    nombre_producto = Column(String, index=True)
    descripcion = Column(String)
    cantidad = Column(Integer)
    precio_unitario = Column(Float)
    fecha_ingreso = Column(Date, default=datetime.date.today)

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
