"""Rota de verificação de disponibilidade para monitoramento."""
from flask import Blueprint, jsonify
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.persistence.database import db_session

bp = Blueprint("saude", __name__)


@bp.get("/saude")
def saude():
    """Responde 200 se o banco atende a uma consulta trivial; 503 caso contrário."""
    try:
        db_session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        db_session.rollback()
        return jsonify(status="erro"), 503
    return jsonify(status="ok"), 200
