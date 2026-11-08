"""Rotas da área do tutor: pets e registros de saúde."""
from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from app.presentation.seguranca import login_required
from app.services import pets as servico_pets
from app.services import registros as servico_registros
from app.services.auth import ErroValidacao

bp = Blueprint("pets", __name__)

CAMPOS_PET = ("nome", "especie", "raca", "data_nascimento")
CAMPOS_REGISTRO = (
    "tipo",
    "descricao",
    "data_registro",
    "proxima_data",
    "dosagem",
    "horario",
    "data_fim",
    "observacoes",
)
ROTULOS_TIPO = {
    "vacina": "Vacina",
    "consulta": "Consulta",
    "medicamento": "Medicamento",
    "exame": "Exame",
}


def _pet_ou_404(id_pet):
    pet = servico_pets.obter_pet(g.usuario.id_usuario, id_pet)
    if pet is None:
        abort(404)
    return pet


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


@bp.route("/pets/<int:id_pet>/registros/novo", methods=["GET", "POST"])
@login_required
def novo_registro(id_pet):
    pet = _pet_ou_404(id_pet)
    erros = {}
    dados = {campo: "" for campo in CAMPOS_REGISTRO}
    if request.method == "POST":
        dados = {campo: request.form.get(campo, "") for campo in CAMPOS_REGISTRO}
        try:
            servico_registros.criar_registro(g.usuario.id_usuario, id_pet, dados)
        except servico_registros.PetNaoEncontrado:
            abort(404)
        except ErroValidacao as erro:
            erros = erro.erros
        else:
            flash("Registro salvo com sucesso", "sucesso")
            return redirect(f"/pets/{pet.id_pet}/historico")
    return render_template(
        "registro_novo.html", pet=pet, erros=erros, dados=dados, rotulos_tipo=ROTULOS_TIPO
    )
