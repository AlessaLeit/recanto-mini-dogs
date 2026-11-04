"""
Painel oculto de contas (rota do frontend: /ale_admin_canil).

Não usa o login normal: exige o cabeçalho X-Admin-Key igual à chave mestra
(ADMIN_PASSWORD do .env). Assim, mesmo que ninguém consiga entrar no sistema
(senha esquecida), quem tem acesso ao servidor consegue recuperar a conta.
"""
import hmac
import re
from typing import List
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session
from app.auth import hash_senha
from app.database import get_db, settings
from app.models.usuario import Usuario

SENHA_MIN = 8
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def exigir_chave_mestra(x_admin_key: str = Header(default="")):
    if not hmac.compare_digest(x_admin_key.encode(), settings.ADMIN_PASSWORD.encode()):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Chave de administração inválida")


router = APIRouter(dependencies=[Depends(exigir_chave_mestra)])


def _checar_senha(v: str) -> str:
    if len(v) < SENHA_MIN:
        raise ValueError(f"A senha precisa ter pelo menos {SENHA_MIN} caracteres")
    return v


class UsuarioCreate(BaseModel):
    email: str
    senha: str

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        v = v.strip().lower()
        if not _EMAIL_RE.match(v) or len(v) > 255:
            raise ValueError("E-mail inválido")
        return v

    @field_validator("senha")
    @classmethod
    def _senha(cls, v: str) -> str:
        return _checar_senha(v)


class SenhaUpdate(BaseModel):
    nova_senha: str

    @field_validator("nova_senha")
    @classmethod
    def _senha(cls, v: str) -> str:
        return _checar_senha(v)


class AtivoUpdate(BaseModel):
    ativo: bool


class UsuarioOut(BaseModel):
    id: int
    email: str
    ativo: bool

    model_config = {"from_attributes": True}


def _obter(db: Session, usuario_id: int) -> Usuario:
    u = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return u


def _outros_ativos(db: Session, usuario_id: int) -> int:
    return db.query(Usuario).filter(Usuario.ativo.is_(True), Usuario.id != usuario_id).count()


@router.get("/usuarios", response_model=List[UsuarioOut])
def listar(db: Session = Depends(get_db)):
    return db.query(Usuario).order_by(Usuario.id).all()


@router.post("/usuarios", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
def criar(dados: UsuarioCreate, db: Session = Depends(get_db)):
    if db.query(Usuario).filter(Usuario.email == dados.email).first():
        raise HTTPException(status_code=409, detail="Já existe uma conta com esse e-mail")
    u = Usuario(email=dados.email, senha_hash=hash_senha(dados.senha))
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@router.put("/usuarios/{usuario_id}/senha", response_model=UsuarioOut)
def alterar_senha(usuario_id: int, dados: SenhaUpdate, db: Session = Depends(get_db)):
    u = _obter(db, usuario_id)
    u.senha_hash = hash_senha(dados.nova_senha)  # também invalida os tokens já emitidos
    db.commit()
    db.refresh(u)
    return u


@router.patch("/usuarios/{usuario_id}", response_model=UsuarioOut)
def ativar_desativar(usuario_id: int, dados: AtivoUpdate, db: Session = Depends(get_db)):
    u = _obter(db, usuario_id)
    if not dados.ativo and u.ativo and _outros_ativos(db, u.id) == 0:
        raise HTTPException(status_code=400, detail="Não é possível desativar a última conta ativa")
    u.ativo = dados.ativo
    db.commit()
    db.refresh(u)
    return u


@router.delete("/usuarios/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir(usuario_id: int, db: Session = Depends(get_db)):
    u = _obter(db, usuario_id)
    if u.ativo and _outros_ativos(db, u.id) == 0:
        raise HTTPException(status_code=400, detail="Não é possível excluir a última conta ativa")
    db.delete(u)
    db.commit()
    return None
