"""Modelos do PetCare: Usuario, Pet e RegistroSaude."""
from datetime import date, time
from typing import Optional

from sqlalchemy import CheckConstraint, Date, ForeignKey, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.persistence.database import Base

TIPOS_REGISTRO = ("vacina", "consulta", "medicamento", "exame")


class Usuario(Base):
    __tablename__ = "usuario"

    id_usuario: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(254), unique=True)
    senha_hash: Mapped[str] = mapped_column(String(255))

    pets: Mapped[list["Pet"]] = relationship(
        back_populates="tutor", cascade="all, delete-orphan"
    )


class Pet(Base):
    __tablename__ = "pet"

    id_pet: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(80))
    especie: Mapped[str] = mapped_column(String(40))
    raca: Mapped[Optional[str]] = mapped_column(String(80))
    data_nascimento: Mapped[Optional[date]] = mapped_column(Date)
    id_usuario: Mapped[int] = mapped_column(
        ForeignKey("usuario.id_usuario", ondelete="CASCADE")
    )

    tutor: Mapped["Usuario"] = relationship(back_populates="pets")
    registros: Mapped[list["RegistroSaude"]] = relationship(
        back_populates="pet", cascade="all, delete-orphan"
    )


class RegistroSaude(Base):
    __tablename__ = "registro_saude"
    __table_args__ = (
        CheckConstraint(
            "tipo IN ('vacina', 'consulta', 'medicamento', 'exame')",
            name="ck_registro_saude_tipo",
        ),
    )

    id_registro: Mapped[int] = mapped_column(primary_key=True)
    id_pet: Mapped[int] = mapped_column(ForeignKey("pet.id_pet", ondelete="CASCADE"))
    tipo: Mapped[str] = mapped_column(String(20))
    descricao: Mapped[str] = mapped_column(String(200))
    data_registro: Mapped[date] = mapped_column(Date)
    proxima_data: Mapped[Optional[date]] = mapped_column(Date)
    dosagem: Mapped[Optional[str]] = mapped_column(String(80))
    horario: Mapped[Optional[time]] = mapped_column(Time)
    data_fim: Mapped[Optional[date]] = mapped_column(Date)
    observacoes: Mapped[Optional[str]] = mapped_column(Text)

    pet: Mapped["Pet"] = relationship(back_populates="registros")
