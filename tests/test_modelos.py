"""Testes de persistência dos modelos Usuario, Pet e RegistroSaude."""
from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app import create_app
from app.persistence.database import db_session
from app.persistence.models import Pet, RegistroSaude, Usuario


@pytest.fixture
def app():
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "chave-de-teste",
            "DATABASE_URL": "sqlite:///:memory:",
        }
    )
    with app.app_context():
        yield app


def novo_usuario(email="ana@exemplo.com"):
    return Usuario(nome="Ana Exemplo", email=email, senha_hash="hash-de-teste")


def test_cria_usuario_pet_e_registro(app):
    usuario = novo_usuario()
    pet = Pet(nome="Bento", especie="Cão", raca="Shih Tzu", tutor=usuario)
    RegistroSaude(
        pet=pet,
        tipo="vacina",
        descricao="Vacina antirrábica (exemplo)",
        data_registro=date(2026, 11, 5),
        proxima_data=date(2027, 11, 5),
    )
    db_session.add(usuario)
    db_session.commit()

    salvo = db_session.get(Usuario, usuario.id_usuario)
    assert salvo.pets[0].nome == "Bento"
    assert salvo.pets[0].registros[0].tipo == "vacina"
    assert salvo.pets[0].registros[0].proxima_data == date(2027, 11, 5)


def test_email_deve_ser_unico(app):
    db_session.add(novo_usuario())
    db_session.commit()

    db_session.add(novo_usuario())
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_tipo_de_registro_invalido_e_rejeitado(app):
    usuario = novo_usuario()
    pet = Pet(nome="Mimi", especie="Gato", tutor=usuario)
    RegistroSaude(
        pet=pet, tipo="outro", descricao="Tipo inválido", data_registro=date(2026, 11, 5)
    )
    db_session.add(usuario)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_remover_usuario_remove_pets_e_registros(app):
    usuario = novo_usuario()
    pet = Pet(nome="Bento", especie="Cão", tutor=usuario)
    RegistroSaude(
        pet=pet, tipo="exame", descricao="Hemograma (exemplo)", data_registro=date(2026, 8, 15)
    )
    db_session.add(usuario)
    db_session.commit()

    db_session.delete(usuario)
    db_session.commit()

    assert db_session.scalars(select(Pet)).all() == []
    assert db_session.scalars(select(RegistroSaude)).all() == []
