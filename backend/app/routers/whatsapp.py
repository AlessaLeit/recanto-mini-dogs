"""
Router WhatsApp - Endpoints administrativos para conectar e monitorar a
instância do Evolution API. Protegidos pelo mesmo JWT do resto do app, então
o Evolution API em si não precisa expor porta pública nenhuma.
"""
from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_user
from app.services import whatsapp_service

router = APIRouter(
    tags=["WhatsApp"],
    redirect_slashes=True,
    dependencies=[Depends(get_current_user)],
)


@router.get("/qrcode")
def obter_qrcode():
    """Retorna o QR code para conectar o WhatsApp (se ainda não conectado)."""
    try:
        return whatsapp_service.obter_qrcode()
    except whatsapp_service.WhatsAppNaoConfigurado:
        raise HTTPException(status_code=503, detail="Integração com WhatsApp não configurada.")
    except whatsapp_service.WhatsAppError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/status")
def obter_status():
    """Retorna o estado de conexão da instância do WhatsApp."""
    try:
        return whatsapp_service.obter_status()
    except whatsapp_service.WhatsAppNaoConfigurado:
        raise HTTPException(status_code=503, detail="Integração com WhatsApp não configurada.")
    except whatsapp_service.WhatsAppError as e:
        raise HTTPException(status_code=502, detail=str(e))
