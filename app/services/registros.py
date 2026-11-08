"""Regras de negócio dos registros de saúde (RF03, RF04). Todo acesso passa pelo pet do tutor."""
import re
from datetime import time

from sqlalchemy import select

from app.persistence.database import db_session
from app.persistence.models import TIPOS_REGISTRO, RegistroSaude
from app.services.auth import ErroValidacao
from app.services.pets import ler_data, obter_pet, texto

PADRAO_HORARIO = re.compile(r"^\d{2}:\d{2}$")


class PetNaoEncontrado(Exception):
    """O pet não existe ou não pertence ao tutor (a rota responde 404)."""


def _pet_do_tutor(id_usuario, id_pet):
    pet = obter_pet(id_usuario, id_pet)
    if pet is None:
        raise PetNaoEncontrado()
    return pet


def _ler_horario(valor):
    valor = texto(valor)
    if not valor:
        return None
    if not PADRAO_HORARIO.match(valor):
        raise ValueError("formato inválido")
    return time.fromisoformat(valor)


def _ler_data_do_campo(dados, campo, erros, obrigatoria=False):
    try:
        valor = ler_data(dados.get(campo))
    except ValueError:
        erros[campo] = "Informe uma data válida"
        return None
    if valor is None and obrigatoria:
        erros[campo] = "Informe a data"
    return valor


def criar_registro(id_usuario, id_pet, dados):
    pet = _pet_do_tutor(id_usuario, id_pet)

    tipo = texto(dados.get("tipo"))
    descricao = texto(dados.get("descricao"))
    observacoes = texto(dados.get("observacoes"))
    erros = {}

    if not tipo:
        erros["tipo"] = "Selecione o tipo"
    elif tipo not in TIPOS_REGISTRO:
        erros["tipo"] = "Selecione um tipo válido"

    if not descricao:
        erros["descricao"] = "Informe a descrição"
    elif len(descricao) > 200:
        erros["descricao"] = "A descrição deve ter até 200 caracteres"

    data_registro = _ler_data_do_campo(dados, "data_registro", erros, obrigatoria=True)
    proxima_data = _ler_data_do_campo(dados, "proxima_data", erros)
    if data_registro and proxima_data and proxima_data < data_registro:
        erros["proxima_data"] = "A próxima data não pode ser anterior à data do registro"

    if len(observacoes) > 1000:
        erros["observacoes"] = "As observações devem ter até 1000 caracteres"

    # Dosagem, horário e data de término só valem para medicamento; nos demais tipos são descartados.
    dosagem = horario = data_fim = None
    if tipo == "medicamento":
        dosagem = texto(dados.get("dosagem")) or None
        if dosagem and len(dosagem) > 80:
            erros["dosagem"] = "A dosagem deve ter até 80 caracteres"
        try:
            horario = _ler_horario(dados.get("horario"))
        except ValueError:
            erros["horario"] = "Informe o horário no formato HH:MM"
        data_fim = _ler_data_do_campo(dados, "data_fim", erros)
        if data_registro and data_fim and data_fim < data_registro:
            erros["data_fim"] = "A data de término não pode ser anterior à data do registro"

    if erros:
        raise ErroValidacao(erros)

    registro = RegistroSaude(
        id_pet=pet.id_pet,
        tipo=tipo,
        descricao=descricao,
        data_registro=data_registro,
        proxima_data=proxima_data,
        dosagem=dosagem,
        horario=horario,
        data_fim=data_fim,
        observacoes=observacoes or None,
    )
    db_session.add(registro)
    db_session.commit()
    return registro


def normalizar_tipo(tipo):
    """Devolve o tipo se for válido; caso contrário, None (equivale a "todos")."""
    tipo = texto(tipo)
    return tipo if tipo in TIPOS_REGISTRO else None


def listar_registros(id_usuario, id_pet, tipo=None):
    """Registros do pet do tutor, do mais recente ao mais antigo, opcionalmente filtrados por tipo."""
    pet = _pet_do_tutor(id_usuario, id_pet)
    consulta = select(RegistroSaude).where(RegistroSaude.id_pet == pet.id_pet)
    tipo = normalizar_tipo(tipo)
    if tipo:
        consulta = consulta.where(RegistroSaude.tipo == tipo)
    consulta = consulta.order_by(
        RegistroSaude.data_registro.desc(), RegistroSaude.id_registro.desc()
    )
    return list(db_session.scalars(consulta))
