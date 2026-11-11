"""Testes da rota /saude usada no monitoramento de disponibilidade."""
from sqlalchemy.exc import OperationalError

from app.persistence.database import db_session
from app.presentation.seguranca import POLITICA_CSP


def test_saude_responde_ok_sem_login(navegador):
    resposta = navegador.cliente.get("/saude")
    assert resposta.status_code == 200
    assert resposta.get_json() == {"status": "ok"}


def test_saude_traz_cabecalhos_de_seguranca(navegador):
    resposta = navegador.cliente.get("/saude")
    assert resposta.headers["Content-Security-Policy"] == POLITICA_CSP
    assert resposta.headers["X-Content-Type-Options"] == "nosniff"
    assert resposta.headers["X-Frame-Options"] == "DENY"
    assert resposta.headers["Referrer-Policy"] == "same-origin"


def test_saude_nao_expoe_dados_do_usuario_logado(entrar_como):
    nav = entrar_como()
    resposta = nav.cliente.get("/saude")
    assert resposta.get_json() == {"status": "ok"}
    assert "tutora@exemplo.com" not in resposta.get_data(as_text=True)


def test_saude_responde_503_se_o_banco_falhar(navegador, monkeypatch):
    def falhar(*_args, **_kwargs):
        raise OperationalError("SELECT 1", {}, Exception("banco indisponível"))

    monkeypatch.setattr(db_session, "execute", falhar)
    resposta = navegador.cliente.get("/saude")
    assert resposta.status_code == 503
    assert resposta.get_json() == {"status": "erro"}
