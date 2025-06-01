from fastapi import APIRouter, HTTPException, Response, Depends
from typing import List
from app.models import (
    Usuario, UsuarioCreate, UsuarioUpdate, UsuarioResponse,
    Rol, RolCreate, RolUpdate, LoginRequest, LoginResponse,
    ChangePasswordRequest, UsuarioStats
)
from app.database import get_connection
from app.kafka_producer import enviar_evento
from app.security import (
    validate_token, hash_password, verify_password,
    require_admin, require_permissions
)
from datetime import datetime

router = APIRouter()

# ==================== RUTAS DE USUARIOS ====================

@router.post("/", response_model=UsuarioResponse, status_code=201)
def crear_usuario(usuario: UsuarioCreate, current_user_payload: dict = Depends(require_admin)):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, nombre FROM roles WHERE id = %s", (usuario.rol_id,))
        rol_info = cur.fetchone()
        if not rol_info:
            raise HTTPException(status_code=400, detail=f"Rol con ID {usuario.rol_id} no encontrado")

        cur.execute("SELECT id FROM usuarios WHERE email = %s", (usuario.email,))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="Email ya registrado")

        password_hash = hash_password(usuario.password)

        cur.execute("""
            INSERT INTO usuarios (nombre, email, password_hash, activo, rol_id)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, created_at, updated_at
        """, (usuario.nombre, usuario.email, password_hash, usuario.activo, usuario.rol_id))
        resultado = cur.fetchone()

        conn.commit()

        usuario_response = UsuarioResponse(
            id=resultado[0],
            nombre=usuario.nombre,
            email=usuario.email,
            activo=usuario.activo,
            rol_id=usuario.rol_id,
            rol_nombre=rol_info[1],
            created_at=resultado[1],
            updated_at=resultado[2]
        )

        evento_kafka = {
            "accion": "USUARIO_CREADO",
            "usuario": usuario_response.dict(),
            "admin_id": current_user_payload.get("sub")
        }
        enviar_evento("usuarios-events", evento_kafka)

        return usuario_response

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
    finally:
        cur.close()
        conn.close()

@router.get("/", response_model=List[UsuarioResponse])
def listar_usuarios(
    activo: bool = None,
    rol_id: int = None,
    current_user_payload: dict = Depends(require_permissions(["ver:usuarios"]))
):
    conn = get_connection()
    cur = conn.cursor()
    try:
        query = """
            SELECT u.id, u.nombre, u.email, u.activo, u.rol_id, r.nombre, u.created_at, u.updated_at
            FROM usuarios u LEFT JOIN roles r ON u.rol_id = r.id WHERE 1=1
        """
        params = []
        if activo is not None:
            query += " AND u.activo = %s"
            params.append(activo)
        if rol_id is not None:
            query += " AND u.rol_id = %s"
            params.append(rol_id)
        query += " ORDER BY u.nombre ASC"

        cur.execute(query, params)
        usuarios_db = cur.fetchall()

        return [UsuarioResponse(
            id=row[0], nombre=row[1], email=row[2], activo=row[3],
            rol_id=row[4], rol_nombre=row[5], created_at=row[6], updated_at=row[7]
        ) for row in usuarios_db]
    finally:
        cur.close()
        conn.close()

@router.get("/{id_usuario}", response_model=UsuarioResponse)
def obtener_usuario_por_id(id_usuario: int, current_user_payload: dict = Depends(require_permissions(["ver:usuarios"]))):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT u.id, u.nombre, u.email, u.activo, u.rol_id, r.nombre, u.created_at, u.updated_at
            FROM usuarios u LEFT JOIN roles r ON u.rol_id = r.id WHERE u.id = %s
        """, (id_usuario,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        return UsuarioResponse(
            id=row[0], nombre=row[1], email=row[2], activo=row[3],
            rol_id=row[4], rol_nombre=row[5], created_at=row[6], updated_at=row[7]
        )
    finally:
        cur.close()
        conn.close()

@router.put("/{id_usuario}", response_model=UsuarioResponse)
def actualizar_usuario(id_usuario: int, usuario_update: UsuarioUpdate, current_user_payload: dict = Depends(require_admin)):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM usuarios WHERE id = %s", (id_usuario,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        campos = []
        valores = []

        if usuario_update.nombre is not None:
            campos.append("nombre = %s")
            valores.append(usuario_update.nombre)

        if usuario_update.email is not None:
            cur.execute("SELECT id FROM usuarios WHERE email = %s AND id != %s", (usuario_update.email, id_usuario))
            if cur.fetchone():
                raise HTTPException(status_code=400, detail="Email ya registrado")
            campos.append("email = %s")
            valores.append(usuario_update.email)

        if usuario_update.password is not None:
            campos.append("password_hash = %s")
            valores.append(hash_password(usuario_update.password))

        if usuario_update.activo is not None:
            campos.append("activo = %s")
            valores.append(usuario_update.activo)

        if usuario_update.rol_id is not None:
            cur.execute("SELECT id FROM roles WHERE id = %s", (usuario_update.rol_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=400, detail="Rol no válido")
            campos.append("rol_id = %s")
            valores.append(usuario_update.rol_id)

        if not campos:
            raise HTTPException(status_code=400, detail="No hay campos para actualizar")

        campos.append("updated_at = %s")
        valores.append(datetime.utcnow())
        valores.append(id_usuario)

        cur.execute(f"""
            UPDATE usuarios SET {', '.join(campos)} WHERE id = %s
            RETURNING id, nombre, email, activo, rol_id, created_at, updated_at
        """, valores)

        row = cur.fetchone()
        conn.commit()

        cur.execute("SELECT nombre FROM roles WHERE id = %s", (row[4],))
        rol_nombre = cur.fetchone()[0]

        return UsuarioResponse(
            id=row[0], nombre=row[1], email=row[2], activo=row[3],
            rol_id=row[4], rol_nombre=rol_nombre, created_at=row[5], updated_at=row[6]
        )
    finally:
        cur.close()
        conn.close()

@router.delete("/{id_usuario}", status_code=204)
def eliminar_usuario(id_usuario: int, current_user_payload: dict = Depends(require_admin)):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM usuarios WHERE id = %s", (id_usuario,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        cur.execute("DELETE FROM usuarios WHERE id = %s", (id_usuario,))
        conn.commit()
        return Response(status_code=204)
    finally:
        cur.close()
        conn.close()

@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT id, nombre, email, password_hash, activo, rol_id FROM usuarios WHERE email = %s
        """, (request.email,))
        user = cur.fetchone()

        if not user or not verify_password(request.password, user[3]):
            raise HTTPException(status_code=401, detail="Credenciales inválidas")

        if not user[4]:
            raise HTTPException(status_code=403, detail="Cuenta inactiva")

        token = validate_token({"sub": user[0], "nombre": user[1], "rol_id": user[5]})
        return LoginResponse(token=token)
    finally:
        cur.close()
        conn.close()

@router.post("/cambiar-password", status_code=204)
def cambiar_password(request: ChangePasswordRequest, current_user_payload: dict = Depends(validate_token)):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT password_hash FROM usuarios WHERE id = %s", (current_user_payload["sub"],))
        result = cur.fetchone()
        if not result or not verify_password(request.password_actual, result[0]):
            raise HTTPException(status_code=403, detail="Contraseña actual incorrecta")

        nueva_hash = hash_password(request.nueva_password)
        cur.execute("UPDATE usuarios SET password_hash = %s, updated_at = %s WHERE id = %s",
                    (nueva_hash, datetime.utcnow(), current_user_payload["sub"]))
        conn.commit()
        return Response(status_code=204)
    finally:
        cur.close()
        conn.close()

@router.get("/stats/general", response_model=UsuarioStats)
def obtener_estadisticas(current_user_payload: dict = Depends(require_admin)):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM usuarios")
        total = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM usuarios WHERE activo = TRUE")
        activos = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM usuarios WHERE activo = FALSE")
        inactivos = cur.fetchone()[0]

        return UsuarioStats(total=total, activos=activos, inactivos=inactivos)
    finally:
        cur.close()
        conn.close()
