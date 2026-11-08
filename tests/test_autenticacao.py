"""Testes do serviço de autenticação (RF01)."""
import pytest

from app.services import auth
from app.services.auth import ContaBloqueada, CredenciaisInvalidas, ErroValidacao

EMAIL = "ana@exemplo.com"
SENHA = "senha-segura-123"


class Relogio:
    def __init__(self):
        self.agora = 1_000_000.0

    def __call__(self):
        return self.agora


@pytest.fixture
def relogio(monkeypatch):
    relogio = Relogio()
    monkeypatch.setattr(auth, "_agora", relogio)
    return relogio


@pytest.fixture
def usuario(app):
    return auth.cadastrar_usuario("Ana Exemplo", EMAIL, SENHA)


def falhar(email, vezes):
    for _ in range(vezes):
        with pytest.raises(CredenciaisInvalidas):
            auth.autenticar(email, "senha-errada")


def test_cadastro_guarda_hash_scrypt_e_nao_a_senha(usuario):
    assert usuario.senha_hash != SENHA
    assert usuario.senha_hash.startswith("scrypt:")


def test_email_e_normalizado_para_minusculas(app):
    novo = auth.cadastrar_usuario("Ana", "  ANA@Exemplo.COM ", SENHA)
    assert novo.email == EMAIL


def test_dados_invalidos_geram_erros_por_campo(app):
    with pytest.raises(ErroValidacao) as erro:
        auth.cadastrar_usuario("", "sem-arroba", "curta")
    assert set(erro.value.erros) == {"nome", "email", "senha"}


def test_email_duplicado_e_rejeitado(usuario):
    with pytest.raises(ErroValidacao) as erro:
        auth.cadastrar_usuario("Outra Pessoa", "ANA@exemplo.com", SENHA)
    assert "email" in erro.value.erros


def test_autentica_com_credenciais_corretas(usuario):
    autenticado = auth.autenticar(EMAIL, SENHA)
    assert autenticado.id_usuario == usuario.id_usuario


def test_senha_errada_e_email_inexistente_dao_o_mesmo_erro(usuario):
    with pytest.raises(CredenciaisInvalidas):
        auth.autenticar(EMAIL, "senha-errada")
    with pytest.raises(CredenciaisInvalidas):
        auth.autenticar("nao-existe@exemplo.com", SENHA)


def test_bloqueia_apos_5_falhas_mesmo_com_senha_correta(usuario, relogio):
    falhar(EMAIL, 5)
    with pytest.raises(ContaBloqueada):
        auth.autenticar(EMAIL, SENHA)


def test_bloqueio_expira_apos_15_minutos(usuario, relogio):
    falhar(EMAIL, 5)
    relogio.agora += 15 * 60 + 1
    assert auth.autenticar(EMAIL, SENHA).id_usuario == usuario.id_usuario


def test_login_correto_zera_as_falhas(usuario, relogio):
    falhar(EMAIL, 4)
    auth.autenticar(EMAIL, SENHA)
    falhar(EMAIL, 4)
