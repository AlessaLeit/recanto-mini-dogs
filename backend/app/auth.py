from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db, settings
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

class Token(BaseModel):
    access_token: str
    token_type: str

def get_current_user(token: str = Depends(oauth2_scheme)):
    """Valida o token JWT. Se for inválido, bloqueia o acesso."""
    try:
        payload = AuthService.decode_token(token)
        if payload.get("sub") != settings.ADMIN_USER:
            raise HTTPException(status_code=401, detail="Usuário não autorizado")
        return payload.get("sub")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/register")
def register():
    """Rota de registro desativada. Credenciais são geridas via .env."""
    raise HTTPException(status_code=403, detail="O registro de novos usuários está desativado.")

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Validação direta contra as variáveis de ambiente
    if form_data.username != settings.ADMIN_USER or form_data.password != settings.ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = AuthService.create_access_token(
        data={"sub": settings.ADMIN_USER}
    )
    return {"access_token": access_token, "token_type": "bearer"}