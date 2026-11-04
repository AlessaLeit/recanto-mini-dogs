"""
Routers FastAPI - Endpoints da API REST.
"""
from fastapi import APIRouter, Depends
from app.auth import get_current_user
from .clientes import router as clientes_router
from .cachorros import router as cachorros_router
from .pacotes import router as pacotes_router
from .banhos import router as banhos_router
from .relatorios import router as relatorios_router
from .agendamentos import router as agendamentos_router
from .auth import router as auth_router
from .whatsapp import router as whatsapp_router
from .comandas import router as comandas_router
from .painel_admin import router as painel_admin_router

# Router principal que agrega todos os sub-routers
api_router = APIRouter()

api_router.include_router(auth_router)  # login: público
# Painel de contas: protegido por chave mestra própria (X-Admin-Key), não por JWT
api_router.include_router(painel_admin_router, prefix="/admin-canil", tags=["Painel Admin"])

# Todos os demais exigem JWT válido (defesa em profundidade: vale mesmo que um
# router novo esqueça de declarar a dependência).
_protegido = [Depends(get_current_user)]
api_router.include_router(clientes_router, prefix="/clientes", tags=["Clientes"], dependencies=_protegido)
api_router.include_router(cachorros_router, prefix="/cachorros", tags=["Cachorros"], dependencies=_protegido)
api_router.include_router(pacotes_router, prefix="/pacotes", tags=["Pacotes"], dependencies=_protegido)
api_router.include_router(banhos_router, prefix="/banhos", tags=["Banhos"], dependencies=_protegido)
api_router.include_router(relatorios_router, prefix="/relatorios", tags=["Relatórios"], dependencies=_protegido)
api_router.include_router(agendamentos_router, prefix="/agendamentos", tags=["Agendamentos"], dependencies=_protegido)
api_router.include_router(whatsapp_router, prefix="/whatsapp", tags=["WhatsApp"], dependencies=_protegido)
api_router.include_router(comandas_router, prefix="/comandas-impressao", tags=["Comandas"], dependencies=_protegido)

__all__ = ["api_router"]