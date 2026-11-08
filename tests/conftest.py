"""Fixtures compartilhadas pelos testes."""
import pytest

from app import create_app
from app.services import auth


@pytest.fixture
def app():
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "chave-de-teste",
            "DATABASE_URL": "sqlite:///:memory:",
        }
    )
    with app.app_context():
        yield app


@pytest.fixture(autouse=True)
def limpar_estado_de_login():
    auth.limpar_tentativas()
    yield
    auth.limpar_tentativas()
