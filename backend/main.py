"""
Backend SIMPLIFICADO FINAL - arquivo único COMPLETO.
Imports corrigidos, tables checkfirst, JSON frontend.
"""

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Annotated
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Date, ForeignKey, DateTime, func
from sqlalchemy.orm import sessionmaker, Session, declarative_base, relationship
from sqlalchemy.pool import StaticPool
from datetime import date, datetime
from enum import Enum

# MODELS
Base = declarative_base()

class TipoPlano(str, Enum):
    SEMANAL = "semanal"
    QUINZENAL = "quinzenal"
    MENSAL = "mensal"

class Cliente(Base):
    __tablename__ = "clientes"
    id = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False)
    telefone = Column(String(20))
    endereco = Column(String(255))
    criado_em = Column(DateTime, server_default=func.now())

class Cachorro(Base):
    __tablename__ = "cachorros"
    id = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    nome = Column(String(100))
    raca = Column(String(50))
    porte = Column(String(20))
    observacoes = Column(String)

class Pacote(Base):
    __tablename__ = "pacotes"
    id = Column(Integer, primary_key=True)
    cachorro_id = Column(Integer, ForeignKey("cachorros.id"))
    tipo_plano = Column(String(20))
    valor_cobrado = Column(Float)
    valor_pago = Column(Float, nullable=True)
    data_pagamento = Column(Date, nullable=True)
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, server_default=func.now())
    
    @property
    def status_pagamento(self) -> str:
        if self.valor_pago is None:
            return "em_aberto"
        return "pago" if self.valor_pago >= self.valor_cobrado else "parcial"

# SCHEMAS (simples)
class ClienteCreate(BaseModel):
    nome: str
    telefone: Optional[str] = None
    endereco: Optional[str] = None

class PacoteCreate(BaseModel):
    cachorro_id: int
    tipo_plano: str
    valor_cobrado: float

# Pydantic v2 from_orm deprecated, use model_validate
def to_dict(obj):
    return {
        **{c.name: getattr(obj, c.name) for c in obj.__table__.columns},
        "status_pagamento": obj.status_pagamento if hasattr(obj, 'status_pagamento') else None
    }

# DB
engine = create_engine(
    "sqlite:///./pacotes_banho_simple.db",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
SessionLocal = sessionmaker(bind=engine)
Base.metadata.create_all(bind=engine, checkfirst=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI(title="PacotesBanho Simplificado")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# ENDPOINTS CLIENTES
@app.post("/api/v1/clientes/")
def criar_cliente(cliente: ClienteCreate, db: Annotated[Session, Depends(get_db)]):
    db_cliente = Cliente(**cliente.model_dump())
    db.add(db_cliente)
    db.commit()
    db.refresh(db_cliente)
    return to_dict(db_cliente)

@app.get("/api/v1/clientes/")
def listar_clientes(
    busca: Annotated[Optional[str], Query()] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    db: Annotated[Session, Depends(get_db)] = None
):
    query = db.query(Cliente)
    if busca:
        query = query.filter(Cliente.nome.ilike(f"%{busca}%"))
    return [to_dict(c) for c in query.offset(skip).limit(limit).all()]

@app.get("/api/v1/clientes/{cliente_id}", responses={404: {"description": "Cliente não encontrado"}})
def get_cliente(cliente_id: int, db: Annotated[Session, Depends(get_db)]):
    c = db.query(Cliente).get(cliente_id)
    if not c:
        raise HTTPException(404, "Cliente não encontrado")
    return to_dict(c)

@app.put("/api/v1/clientes/{cliente_id}", responses={404: {"description": "Cliente não encontrado"}})
def update_cliente(cliente_id: int, data: dict, db: Annotated[Session, Depends(get_db)]):
    c = db.query(Cliente).get(cliente_id)
    if not c:
        raise HTTPException(404)
    for k, v in data.items():
        setattr(c, k, v)
    db.commit()
    db.refresh(c)
    return to_dict(c)

@app.delete("/api/v1/clientes/{cliente_id}", responses={404: {"description": "Cliente não encontrado"}})
def delete_cliente(cliente_id: int, db: Annotated[Session, Depends(get_db)]):
    c = db.query(Cliente).get(cliente_id)
    if not c:
        raise HTTPException(404)
    db.delete(c)
    db.commit()
    return {"deleted": True}

# PACOTES
@app.post("/api/v1/pacotes/", responses={404: {"description": "Cachorro não encontrado"}})
def criar_pacote(p: PacoteCreate, db: Annotated[Session, Depends(get_db)]):
    cachorro = db.query(Cachorro).get(p.cachorro_id)
    if not cachorro:
        raise HTTPException(404, "Crie cachorro primeiro")
    db_p = Pacote(**p.model_dump())
    db.add(db_p)
    db.commit()
    db.refresh(db_p)
    return to_dict(db_p)

@app.get("/api/v1/pacotes/")
def listar_pacotes(ativo: Annotated[Optional[bool], Query()] = True, db: Annotated[Session, Depends(get_db)] = None):
    query = db.query(Pacote)
    if ativo is not None:
        query = query.filter(Pacote.ativo == ativo)
    return [to_dict(p) for p in query.all()]

@app.get("/api/v1/pacotes/{pacote_id}", responses={404: {"description": "Pacote não encontrado"}})
def get_pacote(pacote_id: int, db: Annotated[Session, Depends(get_db)]):
    p = db.query(Pacote).get(pacote_id)
    if not p:
        raise HTTPException(404)
    return to_dict(p)

@app.put("/api/v1/pacotes/{pacote_id}", responses={404: {"description": "Pacote não encontrado"}})
def update_pacote(pacote_id: int, data: dict, db: Annotated[Session, Depends(get_db)]):
    p = db.query(Pacote).get(pacote_id)
    if not p:
        raise HTTPException(404)
    for k, v in data.items():
        setattr(p, k, v)
    db.commit()
    db.refresh(p)
    return to_dict(p)

@app.post("/api/v1/pacotes/{pacote_id}/pagar", responses={404: {"description": "Pacote não encontrado"}})
def pagar_pacote(
    pacote_id: int,
    valor_pago: float,
    data_pagamento: str,
    db: Annotated[Session, Depends(get_db)]
):
    p = db.query(Pacote).get(pacote_id)
    if not p:
        raise HTTPException(404)
    p.valor_pago = valor_pago
    p.data_pagamento = date.fromisoformat(data_pagamento)
    db.commit()
    db.refresh(p)
    return to_dict(p)

@app.delete("/api/v1/pacotes/{pacote_id}", responses={404: {"description": "Pacote não encontrado"}})
def delete_pacote(pacote_id: int, db: Annotated[Session, Depends(get_db)]):
    p = db.query(Pacote).get(pacote_id)
    if not p:
        raise HTTPException(404)
    db.delete(p)
    db.commit()
    return {"deleted": True}

@app.get("/")
def root():
    return {"status": "OK", "docs": "/docs"}

print("Backend simplificado carregado! http://localhost:8000/docs")
