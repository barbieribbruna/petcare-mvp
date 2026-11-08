"""Rotas da área do tutor: pets."""
from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from app.presentation.seguranca import login_required
from app.services import pets as servico_pets
from app.services.auth import ErroValidacao

bp = Blueprint("pets", __name__)

CAMPOS_PET = ("nome", "especie", "raca", "data_nascimento")


@bp.get("/pets")
@login_required
def listar():
    pets = servico_pets.listar_pets(g.usuario.id_usuario)
    return render_template("pets.html", pets=pets)


@bp.route("/pets/novo", methods=["GET", "POST"])
@login_required
def novo():
    erros = {}
    dados = {campo: "" for campo in CAMPOS_PET}
    if request.method == "POST":
        dados = {campo: request.form.get(campo, "") for campo in CAMPOS_PET}
        try:
            servico_pets.criar_pet(g.usuario.id_usuario, **dados)
        except ErroValidacao as erro:
            erros = erro.erros
        else:
            flash("Pet cadastrado com sucesso", "sucesso")
            return redirect(url_for("pets.listar"))
    return render_template("pet_novo.html", erros=erros, dados=dados)
