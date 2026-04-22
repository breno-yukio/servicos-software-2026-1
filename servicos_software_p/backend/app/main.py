from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .models import GerarPlanoRequest
from .planner import gerar_plano

app = FastAPI(
    title="Planejador de Rotina de Estudos",
    version="1.0.0",
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
    return {
        "servico": "planejador-backend",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/gerar-plano")
def gerar_plano_endpoint(payload: GerarPlanoRequest):
    return gerar_plano(payload)
