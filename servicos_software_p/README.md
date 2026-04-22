# Planejador de rotina de estudos

Aplicação com **frontend** (Nginx + HTML/CSS/JS na pasta `gradio-json`) e **backend** (FastAPI na pasta `backend-json`), orquestrada com **Docker Compose** (`compose.yaml`), conforme o projeto final da disciplina.

## Serviços (Compose)

| Serviço Compose | Pasta | Função |
|-----------------|-------|--------|
| `gradio-service` | `gradio-json/` | Página estática + proxy `/api` → backend |
| `backend-json` | `backend-json/` | API REST (`/gerar-plano`, `/health`, `/docs`) |

## Subir localmente

Na pasta `servicos_software_p`:

```bash
docker compose up --build -d
```

- **Interface:** http://localhost:7860 (ajuste a porta em `compose.yaml` se estiver em uso)
- **API (Swagger):** http://localhost:8080/docs  
- **Health:** http://localhost:8080/health ou http://localhost:7860/api/health  

Imagens Docker: `breno-yukio/frontend` e `breno-yukio/backend`.

Se algo não subir: `docker compose ps` e `docker compose logs`.
