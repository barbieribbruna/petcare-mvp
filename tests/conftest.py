"""Fixtures compartilhadas pelos testes."""
import re

import pytest

from app import create_app
from app.services import auth

PADRAO_TOKEN = re.compile(r'name="csrf_token" value="([^"]+)"')
SENHA_PADRAO = "senha-segura-123"


@pytest.fixture
def app():
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "chave-de-teste",
            "DATABASE_URL": "sqlite:///:memory:",
            "SESSION_COOKIE_SECURE": False,
        }
    )
    with app.app_context():
        yield app


@pytest.fixture(autouse=True)
def limpar_estado_de_login():
    auth.limpar_tentativas()
    yield
    auth.limpar_tentativas()


class Navegador:
    """Cliente de teste que obtém o token CSRF de uma página antes de enviar formulários."""

    def __init__(self, cliente):
        self.cliente = cliente
        self.usuario = None

    def token(self, caminho="/entrar"):
        pagina = self.cliente.get(caminho).get_data(as_text=True)
        return PADRAO_TOKEN.search(pagina).group(1)

    def postar(self, caminho, dados, origem=None):
        dados = {**dados, "csrf_token": self.token(origem or caminho)}
        return self.cliente.post(caminho, data=dados)

    def entrar(self, email, senha=SENHA_PADRAO):
        return self.postar("/entrar", {"email": email, "senha": senha})


@pytest.fixture
def navegador(app):
    return Navegador(app.test_client())


@pytest.fixture
def entrar_como(app):
    """Cadastra um tutor fictício e devolve um Navegador já autenticado com ele."""

    def entrar(email="tutora@exemplo.com", nome="Tutora Exemplo"):
        usuario = auth.cadastrar_usuario(nome, email, SENHA_PADRAO)
        nav = Navegador(app.test_client())
        resposta = nav.entrar(email)
        assert resposta.status_code == 302
        nav.usuario = usuario
        return nav

    return entrar
