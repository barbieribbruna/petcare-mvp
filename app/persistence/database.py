"""Configuração do banco de dados (SQLAlchemy 2.0)."""
import sqlite3

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, scoped_session, sessionmaker


class Base(DeclarativeBase):
    pass


db_session = scoped_session(sessionmaker(autoflush=False))


@event.listens_for(Engine, "connect")
def ativar_chaves_estrangeiras(conexao, _registro):
    """O SQLite só respeita chaves estrangeiras se isso for ativado."""
    if isinstance(conexao, sqlite3.Connection):
        cursor = conexao.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def init_db(database_url):
    """Cria o engine, associa à sessão e devolve o engine."""
    engine = create_engine(database_url)
    db_session.remove()
    db_session.configure(bind=engine)
    return engine
