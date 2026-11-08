"""Regras de negócio dos pets (RF02). Toda consulta é restrita ao tutor informado."""
import re
from datetime import date

from sqlalchemy import func, select

from app.persistence.database import db_session
from app.persistence.models import Pet
from app.services.auth import ErroValidacao

PADRAO_DATA = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def texto(valor):
    """Normaliza um valor de formulário para texto sem espaços nas pontas."""
    return (valor or "").strip()


def ler_data(valor):
    """Converte 'AAAA-MM-DD' em date. Devolve None se vazio; levanta ValueError se inválido."""
    valor = texto(valor)
    if not valor:
        return None
    if not PADRAO_DATA.match(valor):
        raise ValueError("formato inválido")
    return date.fromisoformat(valor)


def criar_pet(id_usuario, nome, especie, raca, data_nascimento):
    nome = texto(nome)
    especie = texto(especie)
    raca = texto(raca)

    erros = {}
    if not nome:
        erros["nome"] = "Informe o nome do pet"
    elif len(nome) > 80:
        erros["nome"] = "O nome deve ter até 80 caracteres"
    if not especie:
        erros["especie"] = "Informe a espécie"
    elif len(especie) > 40:
        erros["especie"] = "A espécie deve ter até 40 caracteres"
    if len(raca) > 80:
        erros["raca"] = "A raça deve ter até 80 caracteres"

    nascimento = None
    try:
        nascimento = ler_data(data_nascimento)
    except ValueError:
        erros["data_nascimento"] = "Informe uma data válida no formato AAAA-MM-DD"
    else:
        if nascimento and nascimento > date.today():
            erros["data_nascimento"] = "A data de nascimento não pode ser futura"

    if erros:
        raise ErroValidacao(erros)

    pet = Pet(
        id_usuario=id_usuario,
        nome=nome,
        especie=especie,
        raca=raca or None,
        data_nascimento=nascimento,
    )
    db_session.add(pet)
    db_session.commit()
    return pet


def listar_pets(id_usuario):
    consulta = (
        select(Pet)
        .where(Pet.id_usuario == id_usuario)
        .order_by(func.lower(Pet.nome), Pet.id_pet)
    )
    return list(db_session.scalars(consulta))


def obter_pet(id_usuario, id_pet):
    """Devolve o pet somente se pertencer ao tutor; caso contrário, None."""
    consulta = select(Pet).where(Pet.id_pet == id_pet, Pet.id_usuario == id_usuario)
    return db_session.scalar(consulta)
