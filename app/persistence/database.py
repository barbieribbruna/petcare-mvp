"""Configuração do banco de dados (SQLAlchemy 2.0)."""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, scoped_session, sessionmaker


class Base(DeclarativeBase):
    pass


db_session = scoped_session(sessionmaker(autoflush=False))


def init_db(database_url):
    """Cria o engine, associa à sessão e devolve o engine."""
    engine = create_engine(database_url)
    db_session.remove()
    db_session.configure(bind=engine)
    return engine
