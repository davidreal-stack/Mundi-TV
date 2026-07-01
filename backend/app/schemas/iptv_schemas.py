from pydantic import BaseModel
from typing import Optional

class TokenRequest(BaseModel):
    """Solicitud para generar un token JWT"""
    link: str

    class Config:
        json_schema_extra = {
            "example": {
                "link": "https://example.com/stream.m3u8?token=abc123"
            }
        }

class VerifyRequest(BaseModel):
    """Solicitud para verificar un token JWT"""
    token: str

    class Config:
        json_schema_extra = {
            "example": {
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }

class TokenResponse(BaseModel):
    """Respuesta con token generado"""
    token: str
    expires_in_hours: int


class LinkResponse(BaseModel):
    """Respuesta con el enlace real"""
    link: str


class VerifyResponse(BaseModel):
    """Respuesta de verificación de token"""
    valid: bool
    expires_at: Optional[str] = None
    message: str = "Token válido"
