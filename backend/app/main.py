"""
Ponto de entrada da aplicação FastAPI.
Configura CORS, lifespan e registra todos os routers.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database import engine, Base, ensure_schema_upgrades, settings
from app.routers import api_router
from app.routers import auth
from app.auth import criar_admin_inicial


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerenciamento do ciclo de vida da aplicação.
    Cria tabelas na inicialização (em dev; em prod use Alembic).
    """
    try:
        # Startup: cria tabelas se não existirem
        Base.metadata.create_all(bind=engine)
        # Adiciona colunas novas em tabelas já existentes (sem Alembic em produção)
        ensure_schema_upgrades()
        # Primeira execução: cria a conta inicial a partir do .env
        criar_admin_inicial()
        print("✅ Tabelas verificadas/criadas com sucesso.")
    except Exception as e:
        print(f"❌ Erro ao conectar no banco de dados: {e}")
        # Em Docker, é melhor deixar o container crashar para o restart policy atuar
    
    yield
    # Shutdown: cleanup se necessário


# Instância principal do FastAPI
app = FastAPI(
    title="Banho & Tosa API",
    description="API para gerenciamento de pacotes de banho e tosa para pets",
    version="1.0.0",
    lifespan=lifespan,
    # Em produção não expomos a documentação interativa nem o schema da API
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
    openapi_url=None if settings.is_production else "/openapi.json",
)

# CORS: em dev libera o Vite; em produção só as origens listadas em CORS_ORIGINS
# (vazio = nenhuma origem cruzada, pois o nginx serve front e API na mesma origem).
_dev_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://localhost",
    "http://127.0.0.1",
    "http://frontend",
]
_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
if not settings.is_production:
    _origins = _dev_origins + _origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=False,  # autenticação é por header Bearer, não por cookie
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# Registra todos os routers da API
app.include_router(auth.router, prefix="/api/v1")
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root():
    """Endpoint de health check."""
    return {"message": "Banho & Tosa API"}


@app.get("/health")
def health_check():
    """Health check para monitoramento."""
    return {"status": "healthy"}