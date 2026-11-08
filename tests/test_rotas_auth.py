"""Testes das rotas de cadastro, entrada e saída (RF01) e dos cabeçalhos de segurança."""
import re

from app.presentation.seguranca import POLITICA_CSP
from app.services import auth

EMAIL = "tutora@exemplo.com"
SENHA = "senha-segura-123"


def cadastrar_tutora(nome="Tutora Exemplo"):
    return auth.cadastrar_usuario(nome, EMAIL, SENHA)


def test_post_sem_token_csrf_retorna_400(navegador):
    resposta = navegador.cliente.post("/entrar", data={"email": EMAIL, "senha": SENHA})
    assert resposta.status_code == 400


def test_post_com_token_csrf_errado_retorna_400(navegador):
    navegador.token("/entrar")
    resposta = navegador.cliente.post(
        "/cadastro",
        data={"nome": "Tutora Exemplo", "email": EMAIL, "senha": SENHA, "csrf_token": "falso"},
    )
    assert resposta.status_code == 400


def test_cadastro_valido_redireciona_para_entrar_com_mensagem(navegador):
    resposta = navegador.postar(
        "/cadastro", {"nome": "Tutora Exemplo", "email": EMAIL, "senha": SENHA}
    )
    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/entrar")

    pagina = navegador.cliente.get("/entrar").get_data(as_text=True)
    assert "Cadastro realizado. Entre com seu e-mail e senha." in pagina
    assert 'role="status"' in pagina


def test_cadastro_com_email_invalido_mostra_erro_no_campo(navegador):
    resposta = navegador.postar(
        "/cadastro", {"nome": "Tutora Exemplo", "email": "sem-arroba", "senha": SENHA}
    )
    pagina = resposta.get_data(as_text=True)
    assert resposta.status_code == 200
    assert "Informe um e-mail válido" in pagina
    assert 'id="erro-email" role="alert"' in pagina
    assert 'aria-invalid="true" aria-describedby="erro-email"' in pagina


def test_login_incorreto_mostra_mensagem_generica(navegador):
    cadastrar_tutora()
    resposta = navegador.entrar(EMAIL, "senha-errada")
    assert resposta.status_code == 200
    assert "E-mail ou senha incorretos" in resposta.get_data(as_text=True)


def test_login_correto_acessa_pets(navegador):
    cadastrar_tutora()
    resposta = navegador.entrar(EMAIL, SENHA)
    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/pets")

    resposta = navegador.cliente.get("/pets")
    pagina = resposta.get_data(as_text=True)
    assert resposta.status_code == 200
    assert "Olá, Tutora Exemplo" in pagina
    assert "<h1>Meus pets</h1>" in pagina
    assert "Você ainda não cadastrou pets." in pagina
    assert resposta.headers["Cache-Control"] == "no-store"


def test_pets_sem_login_redireciona_para_entrar(navegador):
    resposta = navegador.cliente.get("/pets")
    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/entrar")


def test_inicio_redireciona_conforme_a_sessao(navegador):
    assert navegador.cliente.get("/").headers["Location"].endswith("/entrar")
    cadastrar_tutora()
    navegador.entrar(EMAIL, SENHA)
    assert navegador.cliente.get("/").headers["Location"].endswith("/pets")


def test_sair_encerra_a_sessao(navegador):
    cadastrar_tutora()
    navegador.entrar(EMAIL, SENHA)

    resposta = navegador.postar("/sair", {}, origem="/pets")
    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/entrar")
    assert navegador.cliente.get("/pets").status_code == 302


def test_sexta_tentativa_apos_cinco_falhas_mostra_bloqueio(navegador):
    cadastrar_tutora()
    for _ in range(5):
        navegador.entrar(EMAIL, "senha-errada")

    resposta = navegador.entrar(EMAIL, SENHA)
    pagina = resposta.get_data(as_text=True)
    assert re.search(r"Muitas tentativas\. Tente novamente em \d+ minuto\(s\)\.", pagina)
    assert navegador.cliente.get("/pets").status_code == 302


def test_respostas_trazem_cabecalhos_de_seguranca(navegador):
    resposta = navegador.cliente.get("/entrar")
    assert resposta.headers["Content-Security-Policy"] == POLITICA_CSP
    assert resposta.headers["X-Content-Type-Options"] == "nosniff"
    assert resposta.headers["X-Frame-Options"] == "DENY"
    assert resposta.headers["Referrer-Policy"] == "same-origin"


def test_html_escapa_nome_com_script(navegador):
    cadastrar_tutora(nome="<script>alert('x')</script>")
    navegador.entrar(EMAIL, SENHA)

    pagina = navegador.cliente.get("/pets").get_data(as_text=True)
    assert "&lt;script&gt;" in pagina
    assert "<script>" not in pagina
