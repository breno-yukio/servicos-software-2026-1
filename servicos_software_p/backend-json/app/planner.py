"""
Geração do plano de estudos: janelas horárias, compromissos, blocos e distribuição por matéria.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal
from urllib.parse import quote_plus

from .models import (
    BlocoSaida,
    DiaSaida,
    DicaPorMateria,
    GerarPlanoRequest,
    GerarPlanoResponse,
    LinkDica,
    MateriaEntrada,
)

# Janelas do período preferido (minutos desde 00:00, intervalo [inicio, fim))
JANELAS_MIN = {
    "manha": (8 * 60 + 0, 12 * 60 + 0),
    "tarde": (13 * 60 + 0, 18 * 60 + 0),
    "noite": (19 * 60 + 0, 22 * 60 + 30),
}

PESO_DIFICULDADE = {"baixa": 1, "media": 2, "alta": 3}

# Fração alvo de teoria (resto são exercícios/prática)
FRACAO_TEORIA = {
    "prova": 0.40,
    "revisao": 0.30,
    "aprendizado": 0.70,
    "trabalho": 0.60,
}


def _minutos_para_hhmm(m: int) -> str:
    m = m % (24 * 60)
    h, mm = divmod(m, 60)
    return f"{h:02d}:{mm:02d}"


def _hhmm_para_minutos(hhmm: str) -> int:
    h, mm = hhmm.split(":")
    return int(h) * 60 + int(mm)


def _texto_busca_seguro(texto: str) -> str:
    """Remove caracteres problemáticos para montar query de busca."""
    t = (texto or "").strip()[:120]
    t = re.sub(r"[\x00-\x1f<>\"]+", " ", t)
    return t.strip()


def montar_dicas_exercicios(materias: list[MateriaEntrada]) -> list[DicaPorMateria]:
    """
    Monta sugestões de links (principalmente buscas) por matéria para achar exercícios.
    Os destinos são sites públicos; o aluno filtra o que for útil.
    """
    resultado: list[DicaPorMateria] = []
    for m in materias:
        nome = _texto_busca_seguro(m.nome)
        if not nome:
            continue
        q_ex = quote_plus(f"{nome} exercícios resolvidos")
        q_yt = quote_plus(f"{nome} exercícios passo a passo")
        q_pdf = quote_plus(f"{nome} lista de exercícios pdf")
        links = [
            LinkDica(
                titulo="Exercícios e listas (Google)",
                url=f"https://www.google.com/search?q={q_ex}",
            ),
            LinkDica(
                titulo="Vídeoaulas com exercícios (YouTube)",
                url=f"https://www.youtube.com/results?search_query={q_yt}",
            ),
            LinkDica(
                titulo="Listas em PDF (Google)",
                url=f"https://www.google.com/search?q={q_pdf}",
            ),
        ]
        resultado.append(DicaPorMateria(materia=m.nome, links=links))
    return resultado


def _subtrair_intervalo(
    livres: list[tuple[int, int]], ocup_inicio: int, ocup_fim: int
) -> list[tuple[int, int]]:
    """Remove [ocup_inicio, ocup_fim) de cada intervalo livre (meio-abertos [a,b))."""
    resultado: list[tuple[int, int]] = []
    for a, b in livres:
        if ocup_fim <= a or ocup_inicio >= b:
            resultado.append((a, b))
            continue
        if ocup_inicio > a:
            resultado.append((a, min(ocup_inicio, b)))
        if ocup_fim < b:
            resultado.append((max(ocup_fim, a), b))
    return [(x, y) for x, y in resultado if y - x >= 1]


def _intervalos_livres_dia(
    req: GerarPlanoRequest, dia: int
) -> list[tuple[int, int]]:
    ws, we = JANELAS_MIN[req.periodo_preferido]
    livres = [(ws, we)]
    for c in req.compromissos:
        if c.dia != dia:
            continue
        ci = _hhmm_para_minutos(c.inicio)
        cf = _hhmm_para_minutos(c.fim)
        # Só corta o que intersecta a janela de estudo
        livres = _subtrair_intervalo(livres, ci, cf)
    livres.sort()
    return livres


def _alocar_minutos_por_peso(
    total_minutos: int, pesos: list[int]
) -> list[int]:
    """Distribui `total_minutos` inteiros proporcionalmente a `pesos` (maior resto)."""
    soma = sum(pesos)
    if soma == 0:
        return [0] * len(pesos)
    exatos = [total_minutos * (p / soma) for p in pesos]
    base = [int(x) for x in exatos]
    diff = total_minutos - sum(base)
    ordem = sorted(range(len(pesos)), key=lambda i: (exatos[i] - base[i]), reverse=True)
    for k in range(diff):
        base[ordem[k % len(ordem)]] += 1
    return base


@dataclass
class EstadoMateria:
    nome: str
    min_teoria: int
    min_exercicios: int
    rem_teoria: int = 0
    rem_exercicios: int = 0

    def __post_init__(self):
        self.rem_teoria = self.min_teoria
        self.rem_exercicios = self.min_exercicios


# Ritmo tipo aula: duas aulas de 50 min, intervalos de 5 e 20 min (repete).
CICLO_TIPO_AULA: list[tuple[int, Literal["estudo", "pausa"]]] = [
    (50, "estudo"),
    (5, "pausa"),
    (50, "estudo"),
    (20, "pausa"),
]


@dataclass
class ContextoGeracao:
    req: GerarPlanoRequest
    materias: list[EstadoMateria] = field(default_factory=list)
    blocos_por_dia: dict[int, list[BlocoSaida]] = field(default_factory=dict)
    last_idx: int | None = None
    alternancia: int = 0


def _escolher_materia(ctx: ContextoGeracao) -> int | None:
    candidatos = [i for i, m in enumerate(ctx.materias) if m.rem_teoria + m.rem_exercicios > 0]
    if not candidatos:
        return None
    outros = [i for i in candidatos if i != ctx.last_idx]
    pool = outros if outros else candidatos
    # Prioriza quem tem mais minutos restantes; alterna desempate com `alternancia`
    pool.sort(
        key=lambda i: (
            -(ctx.materias[i].rem_teoria + ctx.materias[i].rem_exercicios),
            (i + ctx.alternancia) % 997,
        )
    )
    return pool[0]


def _escolher_tipo(ctx: ContextoGeracao, mi: int) -> Literal["teoria", "exercicios"]:
    m = ctx.materias[mi]
    if m.rem_teoria <= 0:
        return "exercicios"
    if m.rem_exercicios <= 0:
        return "teoria"
    alvo = FRACAO_TEORIA[ctx.req.objetivo]
    rem_t = m.rem_teoria
    rem_e = m.rem_exercicios
    proporcao_teoria_na_fila = rem_t / (rem_t + rem_e)
    # Se a fila está mais "teórica" que o alvo, consumimos teoria; senão exercícios
    if proporcao_teoria_na_fila >= alvo:
        return "teoria"
    return "exercicios"


def _duracao_estudo_disponivel(
    ctx: ContextoGeracao,
    tipo: Literal["teoria", "exercicios"],
    mi: int,
    max_dur: int,
    alvo_minutos: int,
) -> int:
    m = ctx.materias[mi]
    cap = m.rem_teoria if tipo == "teoria" else m.rem_exercicios
    return min(alvo_minutos, max_dur, cap)


def gerar_plano(req: GerarPlanoRequest) -> GerarPlanoResponse:
    """
    Monta o plano dia a dia respeitando janela, compromissos e quotas por matéria.

    Ritmo fixo: blocos de 50 min (aula), 5 min entre uma matéria e outra, 20 min após
    cada duas aulas (ciclo 50+5+50+20). O campo `pausas` na entrada é legado e não altera isso.
    """
    observacoes: list[str] = []

    # Orçamento total de estudo (teoria + exercícios), em minutos
    total_orcamento_estudo = int(round(req.dias_estudo * req.horas_por_dia * 60))
    if total_orcamento_estudo < 1:
        total_orcamento_estudo = 1

    pesos = [PESO_DIFICULDADE[m.dificuldade] for m in req.materias]
    minutos_por_materia = _alocar_minutos_por_peso(total_orcamento_estudo, pesos)

    materias: list[EstadoMateria] = []
    alvo_t = FRACAO_TEORIA[req.objetivo]
    for mat, total_mat in zip(req.materias, minutos_por_materia, strict=True):
        t = int(round(total_mat * alvo_t))
        e = total_mat - t
        if e < 0:
            e = 0
            t = total_mat
        materias.append(EstadoMateria(nome=mat.nome, min_teoria=t, min_exercicios=e))

    ctx = ContextoGeracao(
        req=req,
        materias=materias,
    )

    for dia in range(1, req.dias_estudo + 1):
        ctx.blocos_por_dia[dia] = []

    minutos_agendados_teoria_ex = 0

    for dia in range(1, req.dias_estudo + 1):
        fase_ciclo = 0
        livres = _intervalos_livres_dia(req, dia)
        if not livres:
            observacoes.append(
                f"Dia {dia}: nenhum horário livre na janela '{req.periodo_preferido}' "
                "após compromissos; nada foi agendado neste dia."
            )
            continue

        for seg_inicio, seg_fim in livres:
            pos = seg_inicio
            while pos < seg_fim:
                if not any(m.rem_teoria + m.rem_exercicios > 0 for m in ctx.materias):
                    break

                espaco = seg_fim - pos
                dur_alvo, modo = CICLO_TIPO_AULA[fase_ciclo % len(CICLO_TIPO_AULA)]

                if modo == "pausa":
                    if espaco < dur_alvo:
                        observacoes.append(
                            f"Dia {dia}: faltaram {dur_alvo - espaco} min no trecho "
                            f"{_minutos_para_hhmm(pos)}–{_minutos_para_hhmm(seg_fim)} para o descanso "
                            f"de {dur_alvo} min; ele segue no próximo horário livre."
                        )
                        break
                    pb = BlocoSaida(
                        inicio=_minutos_para_hhmm(pos),
                        fim=_minutos_para_hhmm(pos + dur_alvo),
                        tipo="pausa",
                        materia=None,
                    )
                    ctx.blocos_por_dia[dia].append(pb)
                    pos += dur_alvo
                    fase_ciclo += 1
                    continue

                # Bloco de estudo (aula)
                if espaco < 15:
                    break

                mi = _escolher_materia(ctx)
                if mi is None:
                    break

                tipo = _escolher_tipo(ctx, mi)
                dur = _duracao_estudo_disponivel(ctx, tipo, mi, espaco, dur_alvo)

                if dur < 15:
                    outro = "exercicios" if tipo == "teoria" else "teoria"
                    if ctx.materias[mi].rem_teoria + ctx.materias[mi].rem_exercicios > 0:
                        tipo = outro
                        dur = _duracao_estudo_disponivel(ctx, tipo, mi, espaco, dur_alvo)
                    if dur < 15:
                        observacoes.append(
                            f"Dia {dia}: sobraram {espaco} min livres em "
                            f"{_minutos_para_hhmm(pos)}–{_minutos_para_hhmm(seg_fim)}, "
                            "insuficientes para um bloco útil (mín. 15 min)."
                        )
                        break

                inicio_b = pos
                fim_b = pos + dur
                bloco = BlocoSaida(
                    inicio=_minutos_para_hhmm(inicio_b),
                    fim=_minutos_para_hhmm(fim_b),
                    tipo=tipo,
                    materia=ctx.materias[mi].nome,
                )
                ctx.blocos_por_dia[dia].append(bloco)
                if tipo == "teoria":
                    ctx.materias[mi].rem_teoria -= dur
                else:
                    ctx.materias[mi].rem_exercicios -= dur
                minutos_agendados_teoria_ex += dur
                pos = fim_b
                ctx.last_idx = mi
                ctx.alternancia += 1
                fase_ciclo += 1

    restante = sum(m.rem_teoria + m.rem_exercicios for m in ctx.materias)
    if restante > 0:
        observacoes.append(
            f"Não foi possível encaixar {restante} min de estudo restantes "
            "na janela disponível (compromissos + limite diário do período). "
            "Aumente dias/horas, encurte compromissos ou use outro período preferido."
        )

    if total_orcamento_estudo > minutos_agendados_teoria_ex + 5:
        observacoes.append(
            f"Orçamento pedido: {total_orcamento_estudo} min de estudo; "
            f"agendado: {minutos_agendados_teoria_ex} min (teoria + exercícios)."
        )

    dias_saida = [
        DiaSaida(dia=d, blocos=ctx.blocos_por_dia.get(d, []))
        for d in range(1, req.dias_estudo + 1)
    ]

    # Tempo total = soma das durações de todos os blocos gerados (inclui intervalos)
    tempo_total = 0
    for d in dias_saida:
        for b in d.blocos:
            tempo_total += _hhmm_para_minutos(b.fim) - _hhmm_para_minutos(b.inicio)

    return GerarPlanoResponse(
        tempo_total_minutos=tempo_total,
        dias=dias_saida,
        observacoes=observacoes,
        dicas_exercicios=montar_dicas_exercicios(list(req.materias)),
    )
