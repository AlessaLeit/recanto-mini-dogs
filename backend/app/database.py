"""
Configuração do banco de dados usando SQLAlchemy 2.x.
Suporta SQLite (desenvolvimento) e PostgreSQL (produção) via variável de ambiente.
"""
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import StaticPool
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Generator
import os


class Settings(BaseSettings):
    """Configurações da aplicação lidas do .env"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Ignora variáveis extras (ex: do Postgres) sem crashar
    )

    DATABASE_URL: str = "sqlite:///./banho_tosa.db"
    DEBUG: bool = False

    # Segurança e Autenticação
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ADMIN_EMAIL: str
    ADMIN_PASSWORD: str


# Instância global das configurações
settings = Settings()

_database_url = settings.DATABASE_URL

# Criação do engine com configurações específicas para SQLite/PostgreSQL
if _database_url.startswith("sqlite"):
    # SQLite requer check_same_thread=False para uso com FastAPI
    engine = create_engine(
        _database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=settings.DEBUG
    )
else:
    # PostgreSQL ou outros bancos de produção
    engine = create_engine(
        _database_url,
        pool_pre_ping=True,
        echo=settings.DEBUG
    )

# Base declarativa para os modelos - ESSENCIAL!
class Base(DeclarativeBase):
    pass

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


def ensure_schema_upgrades() -> None:
    """
    Adiciona colunas novas em tabelas já existentes.
    `Base.metadata.create_all` só cria tabelas ausentes, não altera as existentes,
    e este projeto não roda Alembic em produção — então os ALTERs simples ficam aqui.
    """
    inspector = inspect(engine)
    colunas_novas = {
        "agendamentos": [("turno", "VARCHAR(10) DEFAULT 'manha'")],
        "cachorros": [("criado_em", "TIMESTAMP")],
    }

    for tabela, colunas in colunas_novas.items():
        if tabela not in inspector.get_table_names():
            continue
        existentes = {c["name"] for c in inspector.get_columns(tabela)}
        for nome_coluna, definicao_sql in colunas:
            if nome_coluna in existentes:
                continue
            with engine.begin() as conn:
                conn.execute(text(f"ALTER TABLE {tabela} ADD COLUMN {nome_coluna} {definicao_sql}"))
            if nome_coluna == "criado_em":
                with engine.begin() as conn:
                    conn.execute(text(f"UPDATE {tabela} SET criado_em = CURRENT_TIMESTAMP WHERE criado_em IS NULL"))