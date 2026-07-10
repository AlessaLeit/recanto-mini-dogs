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
    # 12h: cobre um expediente inteiro sem deslogar a equipe no meio do uso
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 720
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
        "agendamentos": [
            ("turno", "VARCHAR(10) DEFAULT 'manha'"),
            ("pet_nome_avulso", "VARCHAR(100)"),
            ("cliente_nome_avulso", "VARCHAR(100)"),
            ("valor_avulso", "FLOAT"),
        ],
        "cachorros": [("criado_em", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")],
        "pagamentos": [("observacao", "TEXT")],
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

    # 'pacote_id' precisa aceitar NULL para permitir banhos avulsos (sem pacote
    # vinculado). SQLite não suporta ALTER COLUMN diretamente, mas como os bancos
    # de desenvolvimento são recriados do zero isso só afeta produção (Postgres).
    if "agendamentos" in inspector.get_table_names() and engine.dialect.name == "postgresql":
        colunas_info = {c["name"]: c for c in inspector.get_columns("agendamentos")}
        if colunas_info.get("pacote_id", {}).get("nullable") is False:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE agendamentos ALTER COLUMN pacote_id DROP NOT NULL"))

    # 'cachorros.criado_em' foi adicionada numa migração anterior sem DEFAULT no
    # banco (só um backfill pontual), então cachorros novos ficavam com NULL e
    # quebravam a resposta da API. Garante DEFAULT + backfill + NOT NULL sempre,
    # independente de a coluna já existir ou ter acabado de ser criada.
    if "cachorros" in inspector.get_table_names() and engine.dialect.name == "postgresql":
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE cachorros ALTER COLUMN criado_em SET DEFAULT CURRENT_TIMESTAMP"))
            conn.execute(text("UPDATE cachorros SET criado_em = CURRENT_TIMESTAMP WHERE criado_em IS NULL"))
            conn.execute(text("ALTER TABLE cachorros ALTER COLUMN criado_em SET NOT NULL"))