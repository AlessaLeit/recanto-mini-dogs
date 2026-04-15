"""
Configuração do banco de dados usando SQLAlchemy 2.x.
Suporta SQLite (desenvolvimento) e PostgreSQL (produção) via variável de ambiente.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool
from pydantic_settings import BaseSettings
from typing import Generator


class Settings(BaseSettings):
    """Configurações da aplicação lidas do .env"""
    DATABASE_URL: str = "sqlite:///./banho_tosa.db"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Instância global das configurações
settings = Settings()

# Criação do engine com configurações específicas para SQLite/PostgreSQL
if settings.DATABASE_URL.startswith("sqlite"):
    # SQLite requer check_same_thread=False para uso com FastAPI
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=settings.DEBUG
    )
else:
    # PostgreSQL ou outros bancos de produção
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        echo=settings.DEBUG
    )

# Base declarativa para os modelos - ESSENCIAL!
Base = declarative_base()

# Factory de sessões
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator:
    """
    Dependency do FastAPI para injeção de sessão do banco.
    Garante fechamento da sessão após cada requisição.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()