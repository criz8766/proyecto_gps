from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# Modelos para Roles
class RolCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    permisos: List[str] = []

class RolUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    permisos: Optional[List[str]] = None

class Rol(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str] = None
    permisos: List[str] = []
    created_at: datetime
    updated_at: datetime

# Modelos para Usuarios
class UsuarioCreate(BaseModel):
    nombre: str
    email: EmailStr
    password: str
    rol_id: int
    activo: bool = True

class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    rol_id: Optional[int] = None
    activo: Optional[bool] = None

class UsuarioResponse(BaseModel):
    id: int
    nombre: str
    email: str
    activo: bool
    rol_id: int
    rol_nombre: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class Usuario(BaseModel):
    id: int
    nombre: str
    email: str
    password_hash: str
    activo: bool
    rol_id: int
    created_at: datetime
    updated_at: datetime

# Modelo para login
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    message: str
    usuario: UsuarioResponse

# Modelo para cambio de contraseña
class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

# Modelo para estadísticas de usuarios
class UsuarioStats(BaseModel):
    total_usuarios: int
    usuarios_activos: int
    usuarios_inactivos: int
    usuarios_por_rol: dict