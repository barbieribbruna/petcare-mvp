"""Testes do cadastro e da listagem de pets (RF02)."""
from datetime import date, timedelta

import pytest

from app.services import auth, pets
from app.services.auth import ErroValidacao

SENHA = "senha-segura-123"


@pytest.fixture
def tutora(app):
    return auth.cadastrar_usuario("Tutora Exemplo", "tutora@exemplo.com", SENHA)


# Serviço

def test_cria_pet_valido(tutora):
    pet = pets.criar_pet(tutora.id_usuario, " Bento ", "Cão", "Shih Tzu", "2020-03-15")
    assert pet.id_pet is not None
    assert pet.nome == "Bento"
    assert pet.raca == "Shih Tzu"
    assert pet.data_nascimento == date(2020, 3, 15)
    assert pet.id_usuario == tutora.id_usuario


def test_raca_e_data_de_nascimento_sao_opcionais(tutora):
    pet = pets.criar_pet(tutora.id_usuario, "Mimi", "Gato", "", "")
    assert pet.raca is None
    assert pet.data_nascimento is None


def test_nome_e_especie_obrigatorios(tutora):
    with pytest.raises(ErroValidacao) as erro:
        pets.criar_pet(tutora.id_usuario, "  ", "", None, None)
    assert set(erro.value.erros) == {"nome", "especie"}


def test_limites_de_tamanho(tutora):
    with pytest.raises(ErroValidacao) as erro:
        pets.criar_pet(tutora.id_usuario, "a" * 81, "b" * 41, "c" * 81, "")
    assert set(erro.value.erros) == {"nome", "especie", "raca"}


@pytest.mark.parametrize("data_invalida", ["15/03/2020", "2020-02-30", "20200315", "abc"])
def test_data_de_nascimento_em_formato_invalido_e_rejeitada(tutora, data_invalida):
    with pytest.raises(ErroValidacao) as erro:
        pets.criar_pet(tutora.id_usuario, "Bento", "Cão", "", data_invalida)
    assert "data_nascimento" in erro.value.erros


def test_data_de_nascimento_futura_e_rejeitada(tutora):
    amanha = (date.today() + timedelta(days=1)).isoformat()
    with pytest.raises(ErroValidacao) as erro:
        pets.criar_pet(tutora.id_usuario, "Bento", "Cão", "", amanha)
    assert erro.value.erros["data_nascimento"] == "A data de nascimento não pode ser futura"


def test_lista_pets_do_tutor_ordenados_por_nome(tutora):
    pets.criar_pet(tutora.id_usuario, "Mimi", "Gato", "", "")
    pets.criar_pet(tutora.id_usuario, "bento", "Cão", "", "")
    assert [p.nome for p in pets.listar_pets(tutora.id_usuario)] == ["bento", "Mimi"]


# Rotas

def test_cadastro_de_pet_pela_rota_aparece_na_lista(entrar_como):
    nav = entrar_como()
    resposta = nav.postar(
        "/pets/novo",
        {"nome": "Bento", "especie": "Cão", "raca": "Shih Tzu", "data_nascimento": "2020-03-15"},
    )
    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/pets")

    pagina = nav.cliente.get("/pets").get_data(as_text=True)
    assert "Bento" in pagina
    assert "Cão · Shih Tzu" in pagina
    assert "Registrar saúde" in pagina
    assert "Ver histórico" in pagina
    assert "Você ainda não cadastrou pets." not in pagina


def test_formulario_de_pet_mostra_erros_junto_aos_campos(entrar_como):
    nav = entrar_como()
    resposta = nav.postar("/pets/novo", {"nome": "", "especie": "", "raca": "", "data_nascimento": ""})
    pagina = resposta.get_data(as_text=True)
    assert resposta.status_code == 200
    assert 'id="erro-nome" role="alert"' in pagina
    assert 'id="erro-especie" role="alert"' in pagina
    assert "Nome (obrigatório)" in pagina


def test_cadastro_de_pet_exige_login(navegador):
    resposta = navegador.cliente.get("/pets/novo")
    assert resposta.status_code == 302
    assert resposta.headers["Location"].endswith("/entrar")


def test_tutor_b_nao_ve_nem_acessa_pets_do_tutor_a(entrar_como):
    nav_a = entrar_como("tutora@exemplo.com", "Tutora Exemplo")
    nav_b = entrar_como("tutor.b@exemplo.com", "Tutor B Exemplo")

    nav_a.postar("/pets/novo", {"nome": "Bento", "especie": "Cão", "raca": "", "data_nascimento": ""})
    pet_de_a = pets.listar_pets(nav_a.usuario.id_usuario)[0]

    assert pets.obter_pet(nav_b.usuario.id_usuario, pet_de_a.id_pet) is None
    assert pets.obter_pet(nav_a.usuario.id_usuario, pet_de_a.id_pet).nome == "Bento"
    assert pets.listar_pets(nav_b.usuario.id_usuario) == []

    pagina_b = nav_b.cliente.get("/pets").get_data(as_text=True)
    assert "Bento" not in pagina_b
    assert "Você ainda não cadastrou pets." in pagina_b
