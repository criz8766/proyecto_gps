import os
import httpx
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError
from dotenv import load_dotenv
from typing import List

# Construir la ruta al archivo .env que está en la carpeta 'stock'
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path=env_path)

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
API_AUDIENCE = os.getenv("AUTH0_API_AUDIENCE")
ALGORITHMS = ["RS256"]

reusable_oauth2 = HTTPBearer()
jwks_cache = None

# Definición de roles y permisos para el módulo de stock
STOCK_PERMISSIONS = {
    "admin": ["stock:read", "stock:write", "stock:delete", "stock:transfer", "stock:adjust", "stock:reports"],
    "inventario": ["stock:read", "stock:write", "stock:transfer", "stock:adjust", "stock:reports"],
    "vendedor": ["stock:read"],
    "cajero": ["stock:read"]
}


async def get_jwks():
    global jwks_cache
    if AUTH0_DOMAIN is None:
        print("Error: AUTH0_DOMAIN no está configurado.")
        raise HTTPException(status_code=500, detail="Configuración de Auth0 (dominio) incompleta en el servidor.")

    if jwks_cache is None:
        async with httpx.AsyncClient() as client:
            try:
                jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
                print(f"Intentando obtener JWKS desde: {jwks_url}")
                response = await client.get(jwks_url)
                response.raise_for_status()
                jwks_cache = response.json()
                print("JWKS obtenidos y cacheados exitosamente.")
            except httpx.HTTPStatusError as e:
                print(
                    f"Error HTTP al obtener JWKS desde {e.request.url!r}: {e.response.status_code} - {e.response.text}")
                raise HTTPException(status_code=500, detail="Error interno al obtener claves de firma del token.")
            except Exception as e:
                print(f"Excepción no esperada al obtener JWKS: {e}")
                raise HTTPException(status_code=500, detail="Error interno del servidor (JWKS).")
    return jwks_cache


async def validate_token(token: HTTPAuthorizationCredentials = Security(reusable_oauth2)):
    if AUTH0_DOMAIN is None or API_AUDIENCE is None:
        print("Error: AUTH0_DOMAIN o API_AUDIENCE no están configurados.")
        raise HTTPException(
            status_code=500, detail="Variables de configuración de Auth0 no encontradas en el servidor."
        )

    if token is None:
        raise HTTPException(status_code=401, detail="No se proporcionó token de autorización")

    token_value = token.credentials

    try:
        jwks = await get_jwks()
        if not jwks or "keys" not in jwks:
            print("Error: JWKS no se pudieron obtener o están en formato incorrecto.")
            raise HTTPException(status_code=500, detail="Error al obtener la configuración de claves de firma.")

        unverified_header = jwt.get_unverified_header(token_value)
        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
                break

        if rsa_key:
            print("Clave RSA encontrada para la validación del token.")
            payload = jwt.decode(
                token_value,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer=f"https://{AUTH0_DOMAIN}/"
            )
            print("Token validado exitosamente.")
            return payload
        else:
            print("Error: No se pudo encontrar la clave de firma apropiada para el token.")
            all_kids_in_jwks = [key.get("kid") for key in jwks.get("keys", [])]
            print(f"Token 'kid': {unverified_header.get('kid')}. Available 'kids' in JWKS: {all_kids_in_jwks}")
            raise HTTPException(status_code=401, detail="Token inválido: No se pudo encontrar la clave de firma.")

    except jwt.ExpiredSignatureError:
        print("Error: Token ha expirado.")
        raise HTTPException(status_code=401, detail="Token ha expirado.")
    except jwt.JWTClaimsError as e:
        print(f"Error en claims JWT (audience/issuer): {e}")
        raise HTTPException(status_code=401, detail=f"Token inválido: Claims incorrectas ({str(e)}).")
    except JWTError as e:
        print(f"Error de JWT genérico: {e}")
        raise HTTPException(status_code=401, detail=f"Token inválido: {str(e)}")
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Excepción no esperada durante validación de token: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor al validar el token: {str(e)}")


def get_user_role(payload: dict) -> str:
    """Extrae el rol del usuario del payload del token"""
    # En Auth0, los roles pueden estar en diferentes ubicaciones dependiendo de la configuración
    # Aquí asumimos que están en 'https://farmacia.com/roles' (namespace personalizado)
    roles = payload.get('https://farmacia.com/roles', [])
    if not roles:
        # Fallback: intentar obtener desde 'roles' directo
        roles = payload.get('roles', [])

    if not roles:
        return "cajero"  # Rol por defecto con permisos mínimos

    # Devuelve el primer rol encontrado (podrías implementar lógica más compleja)
    return roles[0] if isinstance(roles, list) else roles


def check_permission(user_role: str, required_permission: str) -> bool:
    """Verifica si un rol tiene el permiso requerido"""
    user_permissions = STOCK_PERMISSIONS.get(user_role, [])
    return required_permission in user_permissions


def require_permission(required_permission: str):
    """Decorador para proteger rutas que requieren permisos específicos"""

    async def permission_dependency(current_user_payload: dict = Security(validate_token)):
        user_role = get_user_role(current_user_payload)

        if not check_permission(user_role, required_permission):
            raise HTTPException(
                status_code=403,
                detail=f"Acceso denegado. Rol '{user_role}' no tiene el permiso '{required_permission}'"
            )

        return current_user_payload

    return permission_dependency


# Funciones de validación específicas para stock
async def validate_stock_read(current_user_payload: dict = Security(validate_token)):
    """Valida permisos de lectura para stock"""
    return await require_permission("stock:read")(current_user_payload)


async def validate_stock_write(current_user_payload: dict = Security(validate_token)):
    """Valida permisos de escritura para stock"""
    return await require_permission("stock:write")(current_user_payload)


async def validate_stock_delete(current_user_payload: dict = Security(validate_token)):
    """Valida permisos de eliminación para stock"""
    return await require_permission("stock:delete")(current_user_payload)


async def validate_stock_transfer(current_user_payload: dict = Security(validate_token)):
    """Valida permisos de transferencia para stock"""
    return await require_permission("stock:transfer")(current_user_payload)


async def validate_stock_adjust(current_user_payload: dict = Security(validate_token)):
    """Valida permisos de ajuste para stock"""
    return await require_permission("stock:adjust")(current_user_payload)


async def validate_stock_reports(current_user_payload: dict = Security(validate_token)):
    """Valida permisos de reportes para stock"""
    return await require_permission("stock:reports")(current_user_payload)