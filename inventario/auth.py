from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
import requests

AUTH0_DOMAIN = "TU_DOMINIO.auth0.com"
API_AUDIENCE = "TU_API_AUDIENCE"
ALGORITHMS = ["RS256"]

http_bearer = HTTPBearer()

# Cache de llave pública para evitar fetch repetido
jwks = requests.get(f"https://{AUTH0_DOMAIN}/.well-known/jwks.json").json()

def get_token_auth_header(credentials: HTTPAuthorizationCredentials = Depends(http_bearer)):
    return credentials.credentials

def get_current_user(token: str = Depends(get_token_auth_header)):
    unverified_header = jwt.get_unverified_header(token)

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

    if not rsa_key:
        raise HTTPException(status_code=401, detail="No se encontró la clave adecuada")

    try:
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=ALGORITHMS,
            audience=API_AUDIENCE,
            issuer=f"https://{AUTH0_DOMAIN}/"
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.JWTClaimsError:
        raise HTTPException(status_code=401, detail="Claims inválidos")
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")

    return payload
