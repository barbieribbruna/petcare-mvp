"""Fábrica da aplicação PetCare."""
from flask import Flask

from app.config import Config
from app.persistence import models  # noqa: F401  (registra os modelos no metadata)
from app.persistence.database import Base, db_session, init_db


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    if not app.config.get("SECRET_KEY"):
        raise RuntimeError("Defina a variável de ambiente PETCARE_SECRET_KEY.")

    engine = init_db(app.config["DATABASE_URL"])
    Base.metadata.create_all(engine)

    @app.teardown_appcontext
    def encerrar_sessao(exc=None):
        db_session.remove()

    return app
