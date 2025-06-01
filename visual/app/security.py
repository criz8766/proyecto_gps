
def require_permission(required_permission: str):
    def _require_permission(payload=Depends(get_token_payload)):
        permissions = payload.get("permissions", [])
        if required_permission not in permissions:
            raise HTTPException(status_code=403, detail="Acceso denegado")
        return payload
    return _require_permission
