"""Rotas da área do tutor: pets."""
from flask import Blueprint, render_template

from app.presentation.seguranca import login_required

bp = Blueprint("pets", __name__)


@bp.get("/pets")
@login_required
def listar():
    return render_template("pets.html")
