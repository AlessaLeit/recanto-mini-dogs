from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.auth import create_access_token, verificar_senha
from app.database import get_db
from app.models.usuario import Usuario

router = APIRouter(prefix="/auth", tags=["Autenticação"])

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """
    Endpoint de login: valida e-mail e senha contra a tabela de usuários.
    """
    if not login_data.username or not login_data.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="E-mail e senha são obrigatórios"
        )

    email = login_data.username.strip().lower()
    usuario = db.query(Usuario).filter(Usuario.email == email).first()

    # A verificação roda sempre (mesmo sem usuário) para não vazar, pelo tempo
    # de resposta, quais e-mails existem.
    senha_ok = verificar_senha(login_data.password, usuario.senha_hash if usuario else None)
    if not (usuario and senha_ok and usuario.ativo):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "access_token": create_access_token(usuario),
        "token_type": "bearer",
        "user": {"email": usuario.email}
    }
