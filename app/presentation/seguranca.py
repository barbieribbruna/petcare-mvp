"""Segurança da camada de apresentação: CSRF, usuário da sessão, login_required e cabeçalhos HTTP."""
import secrets
from functools import wraps

from flask import abort, g, redirect, render_template, request, session, url_for

from app.persistence.database import db_session
from app.persistence.models import Usuario

CHAVE_CSRF = "csrf_token"
METODOS_SEGUROS = {"GET", "HEAD", "OPTIONS"}
POLITICA_CSP = (
    "default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; "
    "frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
)


def obter_csrf_token():
    """Devolve o token CSRF da sessão, criando um novo se ainda não existir."""
    token = session.get(CHAVE_CSRF)
    if not token:
        token = secrets.token_urlsafe(32)
        session[CHAVE_CSRF] = token
    return token


def validar_csrf():
    """Rejeita com 400 toda requisição que altera estado sem o token CSRF correto."""
    if request.method in METODOS_SEGUROS:
        return
    esperado = session.get(CHAVE_CSRF, "")
    recebido = request.form.get(CHAVE_CSRF, "")
    if not esperado or not recebido:
        abort(400)
    if not secrets.compare_digest(esperado.encode("utf-8"), recebido.encode("utf-8")):
        abort(400)


def carregar_usuario():
    """Carrega em g.usuario o tutor da sessão (ou None) a cada requisição."""
    g.usuario = None
    id_usuario = session.get("id_usuario")
    if id_usuario is not None:
        g.usuario = db_session.get(Usuario, id_usuario)
        if g.usuario is None:
            session.clear()


def login_required(view):
    """Exige tutor autenticado; caso contrário redireciona para /entrar."""

    @wraps(view)
    def protegida(*args, **kwargs):
        if g.get("usuario") is None:
            return redirect(url_for("auth.entrar"))
        return view(*args, **kwargs)

    return protegida


def aplicar_cabecalhos(resposta):
    resposta.headers["Content-Security-Policy"] = POLITICA_CSP
    resposta.headers["X-Content-Type-Options"] = "nosniff"
    resposta.headers["X-Frame-Options"] = "DENY"
    resposta.headers["Referrer-Policy"] = "same-origin"
    if g.get("usuario") is not None:
        resposta.headers["Cache-Control"] = "no-store"
    return resposta


def _pagina_erro(titulo, mensagem, codigo):
    return render_template("erro.html", titulo=titulo, mensagem=mensagem), codigo


def registrar_seguranca(app):
    app.before_request(carregar_usuario)
    app.before_request(validar_csrf)
    app.after_request(aplicar_cabecalhos)
    app.context_processor(lambda: {"csrf_token": obter_csrf_token})
    app.register_error_handler(
        400,
        lambda _erro: _pagina_erro(
            "Requisição inválida",
            "Não foi possível processar o envio. Volte, recarregue a página e tente novamente.",
            400,
        ),
    )
    app.register_error_handler(
        404,
        lambda _erro: _pagina_erro(
            "Página não encontrada",
            "O endereço acessado não existe ou não está disponível.",
            404,
        ),
    )
