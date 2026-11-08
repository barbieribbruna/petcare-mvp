"""Ponto de entrada para executar o PetCare localmente."""
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
