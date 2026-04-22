from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


def _hhmm_to_minutes(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


class CompromissoEntrada(BaseModel):
    dia: int = Field(ge=1)
    inicio: str = Field(pattern=r"^\d{2}:\d{2}$")
    fim: str = Field(pattern=r"^\d{2}:\d{2}$")

    @model_validator(mode="after")
    def fim_apos_inicio(self):
        if _hhmm_to_minutes(self.fim) <= _hhmm_to_minutes(self.inicio):
            raise ValueError("fim deve ser depois de inicio")
        return self


class MateriaEntrada(BaseModel):
    nome: str = Field(min_length=1, max_length=200)
    dificuldade: Literal["baixa", "media", "alta"]


class GerarPlanoRequest(BaseModel):
    dias_estudo: int = Field(ge=1, le=365)
    horas_por_dia: float = Field(gt=0, le=24)
    objetivo: Literal["prova", "revisao", "trabalho", "aprendizado"]
    pausas: Literal["curtas", "longas", "tipo_aula"] = Field(default="tipo_aula")
    periodo_preferido: Literal["manha", "tarde", "noite"]
    compromissos: list[CompromissoEntrada] = Field(default_factory=list)
    materias: list[MateriaEntrada] = Field(min_length=1)

    @field_validator("pausas", mode="before")
    @classmethod
    def pausas_ou_default(cls, v: object) -> object:
        if v is None or v == "":
            return "tipo_aula"
        return v

    @field_validator("horas_por_dia")
    @classmethod
    def horas_razoavel(cls, v: float) -> float:
        if v > 24:
            raise ValueError("horas_por_dia não pode ultrapassar 24")
        return v

    @model_validator(mode="after")
    def compromissos_dia_valido(self):
        for c in self.compromissos:
            if c.dia > self.dias_estudo:
                raise ValueError(
                    f"compromisso no dia {c.dia} inválido: o plano tem apenas {self.dias_estudo} dia(s)"
                )
        return self


class BlocoSaida(BaseModel):
    inicio: str
    fim: str
    tipo: Literal["teoria", "exercicios", "pausa"]
    materia: str | None = None


class DiaSaida(BaseModel):
    dia: int
    blocos: list[BlocoSaida]


class LinkDica(BaseModel):
    titulo: str
    url: str


class DicaPorMateria(BaseModel):
    materia: str
    links: list[LinkDica]


class GerarPlanoResponse(BaseModel):
    tempo_total_minutos: int
    dias: list[DiaSaida]
    observacoes: list[str]
    dicas_exercicios: list[DicaPorMateria] = Field(default_factory=list)
