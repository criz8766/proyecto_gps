from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import date

class BeneficiarioCreate(BaseModel):
    rut: str = Field(..., min_length=8, max_length=12, description="RUT del beneficiario sin puntos ni guión")
    nombre: str = Field(..., min_length=1, max_length=100, description="Nombre del beneficiario")
    apellido_paterno: str = Field(..., min_length=1, max_length=100, description="Apellido paterno")
    apellido_materno: str = Field(..., min_length=1, max_length=100, description="Apellido materno")
    fecha_nacimiento: date = Field(..., description="Fecha de nacimiento")
    telefono: Optional[str] = Field(None, max_length=20, description="Número de teléfono")
    email: Optional[EmailStr] = Field(None, description="Correo electrónico")
    direccion: Optional[str] = Field(None, max_length=200, description="Dirección completa")
    comuna: str = Field(..., max_length=100, description="Comuna de residencia")
    region: str = Field(..., max_length=100, description="Región de residencia")
    estado: str = Field(default="activo", description="Estado del beneficiario")

    class Config:
        schema_extra = {
            "example": {
                "rut": "12345678K",
                "nombre": "Juan Carlos",
                "apellido_paterno": "González",
                "apellido_materno": "López",
                "fecha_nacimiento": "1985-03-15",
                "telefono": "+56912345678",
                "email": "juan.gonzalez@email.com",
                "direccion": "Av. Libertad 123, Depto 4B",
                "comuna": "Santiago",
                "region": "Metropolitana",
                "estado": "activo"
            }
        }

class BeneficiarioUpdate(BaseModel):
    rut: Optional[str] = Field(None, min_length=8, max_length=12, description="RUT del beneficiario")
    nombre: Optional[str] = Field(None, min_length=1, max_length=100, description="Nombre del beneficiario")
    apellido_paterno: Optional[str] = Field(None, min_length=1, max_length=100, description="Apellido paterno")
    apellido_materno: Optional[str] = Field(None, min_length=1, max_length=100, description="Apellido materno")
    fecha_nacimiento: Optional[date] = Field(None, description="Fecha de nacimiento")
    telefono: Optional[str] = Field(None, max_length=20, description="Número de teléfono")
    email: Optional[EmailStr] = Field(None, description="Correo electrónico")
    direccion: Optional[str] = Field(None, max_length=200, description="Dirección completa")
    comuna: Optional[str] = Field(None, max_length=100, description="Comuna de residencia")
    region: Optional[str] = Field(None, max_length=100, description="Región de residencia")
    estado: Optional[str] = Field(None, description="Estado del beneficiario")

    class Config:
        schema_extra = {
            "example": {
                "telefono": "+56987654321",
                "email": "nuevo.email@email.com",
                "direccion": "Nueva Dirección 456",
                "estado": "activo"
            }
        }

class Beneficiario(BeneficiarioCreate):
    id: int = Field(..., description="ID único del beneficiario")
    fecha_registro: str = Field(..., description="Fecha y hora de registro")

    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "rut": "12345678K",
                "nombre": "Juan Carlos",
                "apellido_paterno": "González",
                "apellido_materno": "López",
                "fecha_nacimiento": "1985-03-15",
                "telefono": "+56912345678",
                "email": "juan.gonzalez@email.com",
                "direccion": "Av. Libertad 123, Depto 4B",
                "comuna": "Santiago",
                "region": "Metropolitana",
                "estado": "activo",
                "fecha_registro": "2024-01-15T10:30:00"
            }
        }