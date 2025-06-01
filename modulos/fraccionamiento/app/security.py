import os
import httpx
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError
from dotenv import load_dotenv

# Cargar variables de entorno desde .env ubicado en la raíz del microservicio 'fraccionamiento'
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path=env_path)

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
API_AUDIENCE = os.getenv("AUTH0_API_AUDIENCE")
ALGORITHMS = ["RS256"]

reusable_oauth2 = HTTPBearer()
jwks_cache = None


async def get_jwks():
    global jwks_cache
    if AUTH0_DOMAIN is None:
        print("Error: AUTH0_DOMAIN no está configurado.")
        raise HTTPException(status_code=500, detail="Configuración de Auth0 incompleta en el servidor.")

    if jwks_cache is None:
        async with httpx.AsyncClient() as client:
            try:
                jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
                print(f"Obteniendo JWKS desde: {jwks_url}")
                response = await client.get(jwks_url)
                response.raise_for_status()
                jwks_cache = response.json()
                print("JWKS cacheados exitosamente.")
            except httpx.HTTPStatusError as e:
                print(f"Error HTTP al obtener JWKS: {e.response.status_code} - {e.response.text}")
                raise HTTPException(status_code=500, detail="No se pudieron obtener las claves de Auth0.")
            except Exception as e:
                print(f"Excepción al obtener JWKS: {e}")
                raise HTTPException(status_code=500, detail="Error interno al obtener claves de firma.")

    return jwks_cache


async def validate_token(token: HTTPAuthorizationCredentials = Security(reusable_oauth2)):
    if AUTH0_DOMAIN is None or API_AUDIENCE is None:
        print("Error: Variables de entorno Auth0 no están configuradas.")
        raise HTTPException(status_code=500, detail="Configuración Auth0 no encontrada en el servidor.")

    if token is None:
        raise HTTPException(status_code=401, detail="Token de autorización no proporcionado.")

    token_value = token.credentials

    try:
        jwks = await get_jwks()
        if not jwks or "keys" not in jwks:
            print("Error: JWKS vacíos o mal formateados.")
            raise HTTPException(status_code=500, detail="Claves públicas no disponibles.")

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
            print("Validando token con clave RSA.")
            payload = jwt.decode(
                token_value,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer=f"https://{AUTH0_DOMAIN}/"
            )
            print("Token válido.")
            return payload
        else:
            print("Error: No se encontró clave RSA válida para el token.")
            raise HTTPException(status_code=401, detail="Token inválido: clave de firma no encontrada.")

    except jwt.ExpiredSignatureError:
        print("Token expirado.")
        raise HTTPException(status_code=401, detail="Token expirado.")
    except jwt.JWTClaimsError as e:
        print(f"Claims inválidos: {e}")
        raise HTTPException(status_code=401, detail=f"Token inválido: {str(e)}.")
    except JWTError as e:
        print(f"Error JWT: {e}")
        raise HTTPException(status_code=401, detail=f"Token inválido: {str(e)}")
    except Exception as e:
        print(f"Excepción inesperada durante validación: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor al validar token.")


def check_permission(required_permission: str):
    """
    Decorator para verificar permisos específicos en el token
    """

    def permission_checker(current_user_payload: dict):
        permissions = current_user_payload.get("permissions", [])
        if required_permission not in permissions:
            raise HTTPException(
                status_code=403,
                detail=f"Acceso denegado. Se requiere el permiso: {required_permission}"
            )
        return current_user_payload

    return permission_checker