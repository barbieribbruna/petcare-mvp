"""Testes do histórico de saúde com filtro por tipo (RF04)."""
import pytest

from app.services import auth, pets, registros
from app.services.registros import PetNaoEncontrado


@pytest.fixture
def tutora(app):
    return auth.cadastrar_usuario("Tutora Exemplo", "tutora@exemplo.com", "senha-segura-123")


@pytest.fixture
def bento(tutora):
    return pets.criar_pet(tutora.id_usuario, "Bento", "Cão", "", "")


def registrar(tutora, pet, tipo, descricao, data, **extras):
    return registros.criar_registro(
        tutora.id_usuario,
        pet.id_pet,
        {"tipo": tipo, "descricao": descricao, "data_registro": data, **extras},
    )


@pytest.fixture
def historico_de_bento(tutora, bento):
    registrar(tutora, bento, "exame", "Hemograma (exemplo)", "2026-08-15")
    registrar(tutora, bento, "vacina", "Vacina antirrábica (exemplo)", "2026-11-05")
    registrar(tutora, bento, "consulta", "Consulta de rotina (exemplo)", "2026-03-10")
    registrar(tutora, bento, "vacina", "Vacina V10 (exemplo)", "2026-11-05")
    return bento


def descricoes(lista):
    return [r.descricao for r in lista]


# Serviço

def test_ordena_do_mais_recente_ao_mais_antigo_com_desempate_por_id(tutora, historico_de_bento):
    lista = registros.listar_registros(tutora.id_usuario, historico_de_bento.id_pet)
    assert descricoes(lista) == [
        "Vacina V10 (exemplo)",
        "Vacina antirrábica (exemplo)",
        "Hemograma (exemplo)",
        "Consulta de rotina (exemplo)",
    ]


def test_filtra_por_tipo(tutora, historico_de_bento):
    lista = registros.listar_registros(tutora.id_usuario, historico_de_bento.id_pet, "vacina")
    assert descricoes(lista) == ["Vacina V10 (exemplo)", "Vacina antirrábica (exemplo)"]
    assert registros.listar_registros(tutora.id_usuario, historico_de_bento.id_pet, "medicamento") == []


@pytest.mark.parametrize("tipo_invalido", [None, "", "outro", "VACINA", "' OR 1=1 --"])
def test_tipo_invalido_equivale_a_todos(tutora, historico_de_bento, tipo_invalido):
    lista = registros.listar_registros(tutora.id_usuario, historico_de_bento.id_pet, tipo_invalido)
    assert len(lista) == 4


def test_servico_nao_lista_historico_do_pet_de_outro_tutor(historico_de_bento):
    outro = auth.cadastrar_usuario("Tutor B Exemplo", "tutor.b@exemplo.com", "senha-segura-123")
    with pytest.raises(PetNaoEncontrado):
        registros.listar_registros(outro.id_usuario, historico_de_bento.id_pet)


# Rotas

def test_pagina_de_historico_mostra_cartoes_em_ordem(entrar_como):
    nav = entrar_como()
    pet = pets.criar_pet(nav.usuario.id_usuario, "Mimi", "Gato", "", "")
    registrar(nav.usuario, pet, "vacina", "Vacina tríplice felina (exemplo)", "2026-11-05", proxima_data="2027-11-05")
    registrar(
        nav.usuario, pet, "medicamento", "Vermífugo (exemplo)", "2026-08-15",
        dosagem="1 comprimido", horario="08:30", data_fim="2026-08-20", observacoes="Dar após a refeição.",
    )

    resposta = nav.cliente.get(f"/pets/{pet.id_pet}/historico")
    pagina = resposta.get_data(as_text=True)
    assert resposta.status_code == 200
    assert "<h1>Histórico de saúde — Mimi</h1>" in pagina
    assert "2 registros, do mais recente ao mais antigo" in pagina
    assert pagina.index("Vacina tríplice felina") < pagina.index("Vermífugo")
    assert "05/11/2026" in pagina
    assert "Próxima data" in pagina and "05/11/2027" in pagina
    assert "1 comprimido" in pagina and "08:30" in pagina and "20/08/2026" in pagina
    assert "Dar após a refeição." in pagina
    assert 'class="selo selo-vacina"' in pagina
    assert "<span>Vacina</span>" in pagina and "<span>Medicamento</span>" in pagina
    assert "Registrar saúde" in pagina
    assert resposta.headers["Cache-Control"] == "no-store"


def test_pagina_de_historico_filtra_por_tipo(entrar_como):
    nav = entrar_como()
    pet = pets.criar_pet(nav.usuario.id_usuario, "Mimi", "Gato", "", "")
    registrar(nav.usuario, pet, "vacina", "Vacina tríplice felina (exemplo)", "2026-11-05")
    registrar(nav.usuario, pet, "exame", "Hemograma (exemplo)", "2026-08-15")

    pagina = nav.cliente.get(f"/pets/{pet.id_pet}/historico?tipo=exame").get_data(as_text=True)
    assert "Hemograma (exemplo)" in pagina
    assert "Vacina tríplice felina" not in pagina
    assert "1 registro, do mais recente ao mais antigo" in pagina
    assert '<option value="exame" selected>' in pagina

    pagina = nav.cliente.get(f"/pets/{pet.id_pet}/historico?tipo=invalido").get_data(as_text=True)
    assert "Hemograma (exemplo)" in pagina and "Vacina tríplice felina" in pagina
    assert '<option value="" selected>Todos</option>' in pagina


def test_estado_vazio_do_historico(entrar_como):
    nav = entrar_como()
    pet = pets.criar_pet(nav.usuario.id_usuario, "Mimi", "Gato", "", "")
    pagina = nav.cliente.get(f"/pets/{pet.id_pet}/historico").get_data(as_text=True)
    assert "Nenhum registro de saúde ainda." in pagina


def test_mensagem_de_sucesso_aparece_no_historico_apos_salvar(entrar_como):
    nav = entrar_como()
    pet = pets.criar_pet(nav.usuario.id_usuario, "Mimi", "Gato", "", "")
    resposta = nav.postar(
        f"/pets/{pet.id_pet}/registros/novo",
        {"tipo": "consulta", "descricao": "Consulta de rotina (exemplo)", "data_registro": "2026-11-05"},
    )
    pagina = nav.cliente.get(resposta.headers["Location"]).get_data(as_text=True)
    assert 'role="status"' in pagina
    assert "Registro salvo com sucesso" in pagina


def test_historico_de_pet_de_outro_tutor_ou_inexistente_retorna_404(entrar_como):
    nav_a = entrar_como("tutora@exemplo.com", "Tutora Exemplo")
    nav_b = entrar_como("tutor.b@exemplo.com", "Tutor B Exemplo")
    pet_de_a = pets.criar_pet(nav_a.usuario.id_usuario, "Bento", "Cão", "", "")
    registrar(nav_a.usuario, pet_de_a, "vacina", "Vacina antirrábica (exemplo)", "2026-11-05")

    resposta = nav_b.cliente.get(f"/pets/{pet_de_a.id_pet}/historico")
    assert resposta.status_code == 404
    assert "Vacina antirrábica" not in resposta.get_data(as_text=True)
    assert nav_b.cliente.get("/pets/9999/historico").status_code == 404
    assert nav_a.cliente.get(f"/pets/{pet_de_a.id_pet}/historico").status_code == 200


def test_historico_exige_login(navegador):
    resposta = navegador.cliente.get("/pets/1/historico")
    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/entrar")
