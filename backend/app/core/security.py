import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Any
import jwt

JWT_SECRET = os.getenv("JWT_SECRET", "tu_clave_secreta_super_segura_change_me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 2

def generate_jwt_token(data: Dict[str, Any] = None) -> str:
    """
    Genera un token JWT con expiración.
    """
    payload = data or {}
    expiration = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    
    payload.update({
        "exp": expiration,
        "iat": datetime.now(timezone.utc),
        "authorized": True
    })
    
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> Dict[str, Any]:
    """
    Verifica la validez de un token JWT.
    
    Raises:
        jwt.ExpiredSignatureError: Si el token ha expirado
        jwt.InvalidTokenError: Si el token es inválido
    """
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
