"""Configuração da aplicação. Segredos vêm de variáveis de ambiente."""
import os


class Config:
    SECRET_KEY = os.environ.get("PETCARE_SECRET_KEY")
    DATABASE_URL = os.environ.get("PETCARE_DATABASE_URL", "sqlite:///petcare.db")
    DEBUG = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # Em produção (HTTPS) mantenha 1. Em teste local por http, use PETCARE_COOKIE_SECURE=0.
    SESSION_COOKIE_SECURE = os.environ.get("PETCARE_COOKIE_SECURE", "1") == "1"
