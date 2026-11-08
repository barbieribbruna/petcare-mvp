"""Testes do registro de saúde (RF03)."""
from datetime import date, time

import pytest

from app.persistence.database import db_session
from app.persistence.models import RegistroSaude
from app.services import auth, pets, registros
from app.services.auth import ErroValidacao
from app.services.registros import PetNaoEncontrado


@pytest.fixture
def tutora(app):
    return auth.cadastrar_usuario("Tutora Exemplo", "tutora@exemplo.com", "senha-segura-123")


@pytest.fixture
def bento(tutora):
    return pets.criar_pet(tutora.id_usuario, "Bento", "Cão", "Shih Tzu", "")


def dados_validos(**extras):
    return {
        "tipo": "vacina",
        "descricao": "Vacina antirrábica (exemplo)",
        "data_registro": "2026-11-05",
        **extras,
    }


def registrar(tutora, pet, **extras):
    return registros.criar_registro(tutora.id_usuario, pet.id_pet, dados_validos(**extras))


def erros_de(tutora, pet, **extras):
    with pytest.raises(ErroValidacao) as erro:
        registrar(tutora, pet, **extras)
    return erro.value.erros


# Criação válida

@pytest.mark.parametrize("tipo", ["vacina", "consulta", "medicamento", "exame"])
def test_cria_registro_valido_de_cada_tipo(tutora, bento, tipo):
    registro = registrar(tutora, bento, tipo=tipo, descricao=f"Registro de {tipo} (exemplo)")
    salvo = db_session.get(RegistroSaude, registro.id_registro)
    assert salvo.tipo == tipo
    assert salvo.id_pet == bento.id_pet
    assert salvo.data_registro == date(2026, 11, 5)


def test_cria_vacina_com_proxima_data_e_observacoes(tutora, bento):
    registro = registrar(tutora, bento, proxima_data="2027-11-05", observacoes="  Sem reações.  ")
    assert registro.proxima_data == date(2027, 11, 5)
    assert registro.observacoes == "Sem reações."


def test_medicamento_guarda_dosagem_horario_e_data_fim(tutora, bento):
    registro = registrar(
        tutora,
        bento,
        tipo="medicamento",
        descricao="Vermífugo (exemplo)",
        dosagem="1 comprimido",
        horario="08:30",
        data_fim="2026-11-10",
    )
    assert registro.dosagem == "1 comprimido"
    assert registro.horario == time(8, 30)
    assert registro.data_fim == date(2026, 11, 10)


# Validações

def test_tipo_invalido_e_rejeitado(tutora, bento):
    assert "tipo" in erros_de(tutora, bento, tipo="outro")


def test_tipo_e_descricao_e_data_sao_obrigatorios(tutora, bento):
    erros = erros_de(tutora, bento, tipo="", descricao="   ", data_registro="")
    assert set(erros) == {"tipo", "descricao", "data_registro"}


def test_descricao_e_observacoes_tem_limite(tutora, bento):
    erros = erros_de(tutora, bento, descricao="a" * 201, observacoes="b" * 1001)
    assert set(erros) == {"descricao", "observacoes"}


@pytest.mark.parametrize("data", ["05/11/2026", "2026-02-30", "ontem"])
def test_data_do_registro_invalida(tutora, bento, data):
    assert "data_registro" in erros_de(tutora, bento, data_registro=data)


def test_proxima_data_anterior_ao_registro_e_rejeitada(tutora, bento):
    erros = erros_de(tutora, bento, proxima_data="2026-11-04")
    assert erros == {"proxima_data": "A próxima data não pode ser anterior à data do registro"}


def test_data_fim_anterior_ao_registro_e_rejeitada(tutora, bento):
    erros = erros_de(tutora, bento, tipo="medicamento", data_fim="2026-11-01")
    assert erros == {"data_fim": "A data de término não pode ser anterior à data do registro"}


@pytest.mark.parametrize("horario", ["8h30", "25:00", "08:30:00"])
def test_horario_invalido_de_medicamento_e_rejeitado(tutora, bento, horario):
    assert "horario" in erros_de(tutora, bento, tipo="medicamento", horario=horario)


def test_dosagem_de_medicamento_tem_limite(tutora, bento):
    assert "dosagem" in erros_de(tutora, bento, tipo="medicamento", dosagem="x" * 81)


def test_campos_de_medicamento_sao_descartados_em_outros_tipos(tutora, bento):
    registro = registrar(
        tutora,
        bento,
        tipo="consulta",
        descricao="Consulta de rotina (exemplo)",
        dosagem="x" * 200,
        horario="invalido",
        data_fim="2020-01-01",
    )
    assert registro.dosagem is None
    assert registro.horario is None
    assert registro.data_fim is None


# Isolamento entre tutores

def test_servico_nao_registra_no_pet_de_outro_tutor(tutora, bento):
    outro = auth.cadastrar_usuario("Tutor B Exemplo", "tutor.b@exemplo.com", "senha-segura-123")
    with pytest.raises(PetNaoEncontrado):
        registros.criar_registro(outro.id_usuario, bento.id_pet, dados_validos())
    with pytest.raises(PetNaoEncontrado):
        registros.criar_registro(tutora.id_usuario, 9999, dados_validos())


def test_rota_de_registro_salva_e_redireciona_para_historico(entrar_como):
    nav = entrar_como()
    pet = pets.criar_pet(nav.usuario.id_usuario, "Mimi", "Gato", "", "")
    caminho = f"/pets/{pet.id_pet}/registros/novo"

    pagina = nav.cliente.get(caminho).get_data(as_text=True)
    assert "<h1>Registrar saúde — Mimi</h1>" in pagina
    assert "Tipo (obrigatório)" in pagina
    assert "Se for medicamento" in pagina

    resposta = nav.postar(caminho, dados_validos(tipo="exame", descricao="Hemograma (exemplo)"))
    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith(f"/pets/{pet.id_pet}/historico")
    assert db_session.query(RegistroSaude).filter_by(id_pet=pet.id_pet).count() == 1


def test_rota_de_registro_mostra_erros_junto_aos_campos(entrar_como):
    nav = entrar_como()
    pet = pets.criar_pet(nav.usuario.id_usuario, "Mimi", "Gato", "", "")
    resposta = nav.postar(f"/pets/{pet.id_pet}/registros/novo", dados_validos(tipo="outro"))
    pagina = resposta.get_data(as_text=True)
    assert resposta.status_code == 200
    assert 'id="erro-tipo" role="alert"' in pagina


def test_usuario_b_nao_registra_saude_no_pet_de_a(entrar_como):
    nav_a = entrar_como("tutora@exemplo.com", "Tutora Exemplo")
    nav_b = entrar_como("tutor.b@exemplo.com", "Tutor B Exemplo")
    pet_de_a = pets.criar_pet(nav_a.usuario.id_usuario, "Bento", "Cão", "", "")
    caminho = f"/pets/{pet_de_a.id_pet}/registros/novo"

    assert nav_b.cliente.get(caminho).status_code == 404
    resposta = nav_b.postar(caminho, dados_validos(), origem="/pets")
    assert resposta.status_code == 404
    assert db_session.query(RegistroSaude).count() == 0
