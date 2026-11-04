"""Testes de segurança: rotas protegidas, login por usuários, painel admin e produção."""
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import get_current_user
from app.database import Base, Settings, get_db, settings
from app.main import app
from app.models import Usuario  # noqa: F401  (registra a tabela no metadata)

ROTAS_PROTEGIDAS = [
    "/api/v1/clientes/",
    "/api/v1/cachorros/",
    "/api/v1/pacotes/",
    "/api/v1/banhos/",
    "/api/v1/agendamentos/",
    "/api/v1/relatorios/mensal?ano=2024&mes=5",
    "/api/v1/whatsapp/status",
    "/api/v1/comandas-impressao/pendentes",
]

PAINEL = "/api/v1/admin-canil/usuarios"
CHAVE = {"X-Admin-Key": settings.ADMIN_PASSWORD}


@pytest.fixture
def client_sem_auth():
    """Client com banco próprio em memória e SEM o override de autenticação."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def _db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    anteriores = {
        get_db: app.dependency_overrides.get(get_db),
        get_current_user: app.dependency_overrides.pop(get_current_user, None),
    }
    app.dependency_overrides[get_db] = _db
    try:
        yield TestClient(app)
    finally:
        for dep, original in anteriores.items():
            if original is None:
                app.dependency_overrides.pop(dep, None)
            else:
                app.dependency_overrides[dep] = original
        Base.metadata.drop_all(bind=engine)


def _criar(client, email="ale@canil.com", senha="senha-boa-123"):
    r = client.post(PAINEL, json={"email": email, "senha": senha}, headers=CHAVE)
    assert r.status_code == 201, r.text
    return r.json()


def _login(client, email="ale@canil.com", senha="senha-boa-123"):
    return client.post("/api/v1/auth/login", json={"username": email, "password": senha})


# --- Rotas protegidas -------------------------------------------------------

@pytest.mark.parametrize("rota", ROTAS_PROTEGIDAS)
def test_rotas_exigem_token(client_sem_auth, rota):
    assert client_sem_auth.get(rota).status_code == 401


def test_token_invalido_e_rejeitado(client_sem_auth):
    resp = client_sem_auth.get("/api/v1/clientes/", headers={"Authorization": "Bearer lixo"})
    assert resp.status_code == 401


def test_health_continua_publico(client_sem_auth):
    assert client_sem_auth.get("/health").status_code == 200


# --- Login com usuários do banco ---------------------------------------------

def test_login_ok_e_acesso_com_token(client_sem_auth):
    _criar(client_sem_auth)
    r = _login(client_sem_auth)
    assert r.status_code == 200
    token = r.json()["access_token"]
    ok = client_sem_auth.get("/api/v1/clientes/", headers={"Authorization": f"Bearer {token}"})
    assert ok.status_code == 200


def test_login_senha_errada_e_email_inexistente(client_sem_auth):
    _criar(client_sem_auth)
    assert _login(client_sem_auth, senha="errada-errada").status_code == 401
    assert _login(client_sem_auth, email="outro@canil.com").status_code == 401


def test_email_do_login_ignora_maiusculas(client_sem_auth):
    _criar(client_sem_auth)
    assert _login(client_sem_auth, email="ALE@Canil.com").status_code == 200


def test_trocar_senha_invalida_token_antigo_e_vale_a_nova(client_sem_auth):
    u = _criar(client_sem_auth)
    token = _login(client_sem_auth).json()["access_token"]
    r = client_sem_auth.put(f"{PAINEL}/{u['id']}/senha", json={"nova_senha": "nova-senha-456"}, headers=CHAVE)
    assert r.status_code == 200
    antigo = client_sem_auth.get("/api/v1/clientes/", headers={"Authorization": f"Bearer {token}"})
    assert antigo.status_code == 401
    assert _login(client_sem_auth, senha="senha-boa-123").status_code == 401
    assert _login(client_sem_auth, senha="nova-senha-456").status_code == 200


def test_conta_desativada_nao_entra_nem_usa_token(client_sem_auth):
    _criar(client_sem_auth, email="a@canil.com")
    u2 = _criar(client_sem_auth, email="b@canil.com")
    token = _login(client_sem_auth, email="b@canil.com").json()["access_token"]
    assert client_sem_auth.patch(f"{PAINEL}/{u2['id']}", json={"ativo": False}, headers=CHAVE).status_code == 200
    assert _login(client_sem_auth, email="b@canil.com").status_code == 401
    assert client_sem_auth.get("/api/v1/clientes/", headers={"Authorization": f"Bearer {token}"}).status_code == 401


# --- Painel admin -------------------------------------------------------------

@pytest.mark.parametrize("headers", [{}, {"X-Admin-Key": "chave-errada"}])
def test_painel_exige_chave_mestra(client_sem_auth, headers):
    assert client_sem_auth.get(PAINEL, headers=headers).status_code == 403
    r = client_sem_auth.post(PAINEL, json={"email": "x@x.com", "senha": "senha-boa-123"}, headers=headers)
    assert r.status_code == 403


def test_painel_nao_vaza_hash_da_senha(client_sem_auth):
    _criar(client_sem_auth)
    lista = client_sem_auth.get(PAINEL, headers=CHAVE).json()
    assert lista and all(set(i) == {"id", "email", "ativo"} for i in lista)


def test_painel_valida_entrada_e_duplicidade(client_sem_auth):
    _criar(client_sem_auth)
    assert client_sem_auth.post(PAINEL, json={"email": "ale@canil.com", "senha": "outra-senha-1"}, headers=CHAVE).status_code == 409
    assert client_sem_auth.post(PAINEL, json={"email": "nao-e-email", "senha": "senha-boa-123"}, headers=CHAVE).status_code == 422
    assert client_sem_auth.post(PAINEL, json={"email": "c@canil.com", "senha": "curta"}, headers=CHAVE).status_code == 422


def test_painel_protege_a_ultima_conta_ativa(client_sem_auth):
    u = _criar(client_sem_auth)
    assert client_sem_auth.patch(f"{PAINEL}/{u['id']}", json={"ativo": False}, headers=CHAVE).status_code == 400
    assert client_sem_auth.delete(f"{PAINEL}/{u['id']}", headers=CHAVE).status_code == 400
    outro = _criar(client_sem_auth, email="b@canil.com")
    assert client_sem_auth.delete(f"{PAINEL}/{outro['id']}", headers=CHAVE).status_code == 204


# --- Configuração de produção -------------------------------------------------

def test_producao_recusa_segredos_fracos():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, APP_ENV="production", SECRET_KEY="curta",
                 ADMIN_EMAIL="a@a.com", ADMIN_PASSWORD="senhaforte-123456")
    with pytest.raises(ValidationError):
        Settings(_env_file=None, APP_ENV="production", SECRET_KEY="k" * 40,
                 ADMIN_EMAIL="a@a.com", ADMIN_PASSWORD="curta")


def test_producao_aceita_segredos_fortes():
    s = Settings(_env_file=None, APP_ENV="production", SECRET_KEY="k" * 40,
                 ADMIN_EMAIL="a@a.com", ADMIN_PASSWORD="senhaforte-123456")
    assert s.is_production


def test_admin_inicial_so_e_criado_com_tabela_vazia(monkeypatch):
    import app.auth as auth_mod
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    monkeypatch.setattr(auth_mod, "SessionLocal", Session)

    auth_mod.criar_admin_inicial()
    auth_mod.criar_admin_inicial()  # segunda chamada não duplica

    db = Session()
    try:
        usuarios = db.query(Usuario).all()
        assert [u.email for u in usuarios] == [settings.ADMIN_EMAIL.strip().lower()]
        assert auth_mod.verificar_senha(settings.ADMIN_PASSWORD, usuarios[0].senha_hash)
        assert usuarios[0].senha_hash != settings.ADMIN_PASSWORD
    finally:
        db.close()
