"""Rotas de cadastro, entrada e saída (RF01)."""
import math

from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for

from app.services import auth

bp = Blueprint("auth", __name__)


@bp.get("/")
def inicio():
    if g.get("usuario") is not None:
        return redirect(url_for("pets.listar"))
    return redirect(url_for("auth.entrar"))


@bp.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    erros = {}
    dados = {"nome": "", "email": ""}
    if request.method == "POST":
        dados = {
            "nome": request.form.get("nome", ""),
            "email": request.form.get("email", ""),
        }
        try:
            auth.cadastrar_usuario(dados["nome"], dados["email"], request.form.get("senha", ""))
        except auth.ErroValidacao as erro:
            erros = erro.erros
        else:
            flash("Cadastro realizado. Entre com seu e-mail e senha.", "sucesso")
            return redirect(url_for("auth.entrar"))
    return render_template("cadastro.html", erros=erros, dados=dados)


@bp.route("/entrar", methods=["GET", "POST"])
def entrar():
    erro = None
    email = ""
    if request.method == "POST":
        email = request.form.get("email", "")
        try:
            usuario = auth.autenticar(email, request.form.get("senha", ""))
        except auth.CredenciaisInvalidas:
            erro = "E-mail ou senha incorretos"
        except auth.ContaBloqueada as bloqueio:
            minutos = math.ceil(bloqueio.segundos_restantes / 60)
            erro = f"Muitas tentativas. Tente novamente em {minutos} minuto(s)."
        else:
            session.clear()
            session["id_usuario"] = usuario.id_usuario
            return redirect(url_for("pets.listar"))
    return render_template("entrar.html", erro=erro, email=email)


@bp.post("/sair")
def sair():
    session.clear()
    return redirect(url_for("auth.entrar"))
