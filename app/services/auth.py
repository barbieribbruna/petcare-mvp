"""Regras de negócio da autenticação (RF01)."""
import re
import time

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from app.persistence.database import db_session
from app.persistence.models import Usuario

MAX_TENTATIVAS = 5
JANELA_SEGUNDOS = 15 * 60
SENHA_MINIMA = 8
SENHA_MAXIMA = 128
PADRAO_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Hash descartável: igualar o tempo de resposta quando o e-mail não existe.
_HASH_FALSO = generate_password_hash("senha-falsa-para-igualar-tempo", method="scrypt")

# Tentativas de login com falha, por e-mail (em memória; zera se o servidor reiniciar).
_tentativas = {}


class ErroValidacao(Exception):
    """Dados inválidos. 'erros' mapeia o nome do campo à mensagem."""

    def __init__(self, erros):
        super().__init__("Dados inválidos")
        self.erros = erros


class CredenciaisInvalidas(Exception):
    """E-mail ou senha incorretos."""


class ContaBloqueada(Exception):
    """Excesso de tentativas. 'segundos_restantes' indica quando liberar."""

    def __init__(self, segundos_restantes):
        super().__init__("Conta temporariamente bloqueada")
        self.segundos_restantes = segundos_restantes


def _agora():
    return time.time()


def limpar_tentativas():
    _tentativas.clear()


def _falhas_recentes(email):
    limite = _agora() - JANELA_SEGUNDOS
    recentes = [t for t in _tentativas.get(email, []) if t > limite]
    if recentes:
        _tentativas[email] = recentes
    else:
        _tentativas.pop(email, None)
    return recentes


def cadastrar_usuario(nome, email, senha):
    nome = (nome or "").strip()
    email = (email or "").strip().lower()
    senha = senha or ""

    erros = {}
    if not nome:
        erros["nome"] = "Informe o nome"
    elif len(nome) > 100:
        erros["nome"] = "O nome deve ter até 100 caracteres"
    if len(email) > 254 or not PADRAO_EMAIL.match(email):
        erros["email"] = "Informe um e-mail válido"
    if len(senha) < SENHA_MINIMA:
        erros["senha"] = f"A senha deve ter pelo menos {SENHA_MINIMA} caracteres"
    elif len(senha) > SENHA_MAXIMA:
        erros["senha"] = f"A senha deve ter até {SENHA_MAXIMA} caracteres"
    if erros:
        raise ErroValidacao(erros)

    usuario = Usuario(
        nome=nome,
        email=email,
        senha_hash=generate_password_hash(senha, method="scrypt"),
    )
    db_session.add(usuario)
    try:
        db_session.commit()
    except IntegrityError:
        db_session.rollback()
        raise ErroValidacao({"email": "Não foi possível cadastrar com este e-mail"})
    return usuario


def autenticar(email, senha):
    email = (email or "").strip().lower()

    recentes = _falhas_recentes(email)
    if len(recentes) >= MAX_TENTATIVAS:
        restante = int(recentes[0] + JANELA_SEGUNDOS - _agora()) + 1
        raise ContaBloqueada(restante)

    usuario = db_session.scalar(select(Usuario).where(Usuario.email == email))
    hash_conferido = usuario.senha_hash if usuario else _HASH_FALSO
    senha_valida = check_password_hash(hash_conferido, senha or "")

    if usuario is None or not senha_valida:
        _tentativas.setdefault(email, []).append(_agora())
        raise CredenciaisInvalidas()

    _tentativas.pop(email, None)
    return usuario
