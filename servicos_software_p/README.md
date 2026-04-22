# Planejador de rotina de estudos

Aplicação com **frontend** (Nginx + HTML/CSS/JS na pasta `gradio-json`) e **backend** (FastAPI na pasta `backend-json`), usando Docker Compose. Os manifests Kubernetes (`*-deployment.yaml`, `*-service.yaml`) correspondem a esses serviços.

## Serviços (Compose)

| Serviço Compose | Pasta | Função |
|-----------------|-------|--------|
| `gradio-service` | `gradio-json/` | Página estática + proxy `/api` → backend |
| `backend-json` | `backend-json/` | API `/gerar-plano`, `/health`, `/docs` |

## Subir localmente

Na pasta `servicos_software_p`:

```bash
docker compose up --build -d
```

- **Interface:** http://localhost:7860 (mapeamento `7860:80`; altere em `compose.yaml` se a porta estiver ocupada)
- **API direta:** http://localhost:8080/docs  
- **Health:** http://localhost:8080/health ou http://localhost:7860/api/health  

Imagens: `breno-yukio/frontend` e `breno-yukio/backend`.

## Kubernetes

- Backend: Service `backend-json`, porta **8080**
- Frontend: Service `gradio-service`, porta **80** → `targetPort` **80**

Se algo não subir, verifique `docker compose ps` e `docker compose logs`.
