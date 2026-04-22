"""FastAPI: geração de plano e healthcheck."""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .models import GerarPlanoRequest
from .planner import gerar_plano

app = FastAPI(
    title="Planejador de Rotina de Estudos",
    version="1.0.0",
    description="API para gerar planos de estudo personalizados com base em disponibilidade, "
    "matérias e compromissos.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Converte erros de validação Pydantic em mensagens mais legíveis."""
    erros = []
    for err in exc.errors():
        loc = " → ".join(str(x) for x in err.get("loc", []))
        msg = err.get("msg", "valor inválido")
        erros.append(f"{loc}: {msg}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "erro": "Os dados enviados não puderam ser validados.",
            "detalhes": erros,
        },
    )


@app.get("/")
def root():
    """Identificação rápida do serviço (útil em testes e probes genéricos)."""
    return {
        "servico": "planejador-backend",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health():
    """Verificação simples de disponibilidade do serviço."""
    return {"status": "ok"}


@app.post("/gerar-plano")
def gerar_plano_endpoint(payload: GerarPlanoRequest):
    """
    Recebe preferências do aluno e retorna um cronograma dia a dia com blocos
    de teoria, exercícios e intervalos (definidos automaticamente) com horários reais.
    """
    return gerar_plano(payload)
