import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import settings, get_db, SessionLocal
from app.models.usuario import Usuario

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# Hash fictício para gastar o mesmo tempo quando o e-mail não existe
_HASH_FALSO = pwd_context.hash("senha-falsa-para-igualar-tempo")


class TokenData(BaseModel):
    email: Optional[str] = None


def hash_senha(senha: str) -> str:
    return pwd_context.hash(senha)


def verificar_senha(senha: str, senha_hash: Optional[str]) -> bool:
    """Verifica a senha; com hash ausente ainda gasta tempo equivalente."""
    confere = pwd_context.verify(senha, senha_hash or _HASH_FALSO)
    return confere and senha_hash is not None


def _impressao_senha(senha_hash: str) -> str:
    """Identificador curto da senha atual: trocar a senha invalida tokens antigos."""
    return hashlib.sha256(senha_hash.encode()).hexdigest()[:16]


def create_access_token(usuario: Usuario) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    claims = {"sub": usuario.email, "pv": _impressao_senha(usuario.senha_hash), "exp": expire}
    return jwt.encode(claims, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise credentials_exception

    email = payload.get("sub")
    if not email:
        raise credentials_exception

    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if (
        usuario is None
        or not usuario.ativo
        or payload.get("pv") != _impressao_senha(usuario.senha_hash)
    ):
        raise credentials_exception
    return usuario.email


def criar_admin_inicial() -> None:
    """
    Se a tabela de usuários estiver vazia, cria a primeira conta com
    ADMIN_EMAIL / ADMIN_PASSWORD do .env (mantém instalações existentes funcionando).
    """
    db = SessionLocal()
    try:
        if db.query(Usuario).count() == 0:
            db.add(Usuario(
                email=settings.ADMIN_EMAIL.strip().lower(),
                senha_hash=hash_senha(settings.ADMIN_PASSWORD),
            ))
            db.commit()
    finally:
        db.close()
