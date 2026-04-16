# Áudio → texto (Gradio + FastAPI + Whisper)

Manda um áudio (grava ou faz upload) e recebe o texto em português. Dá pra usar como base de prompt pra IA.

**Front (7860):** Gradio — só a interface. Ele manda o arquivo pro back com `requests` (`POST` em `/transcrever`).  
**Back (8080):** FastAPI + Whisper — aqui roda a transcrição e volta `{"texto": "..."}`.

**APIs do back:** `GET /` (só pra ver se subiu, o Gradio não usa) e **`POST /transcrever`** (a rota que o front chama; áudio no campo `file`). Separamos assim porque o back fica testável e reutilizável sem carregar modelo na mesma app da UI.

## Rodar

```sh
docker compose up -d --build
```

- App: http://localhost:7860  
- API: http://localhost:8080 · doc rápida: http://localhost:8080/docs  

**Env úteis:** `WHISPER_MODEL` (back), `BACKEND_URL` e `TRANSCRICAO_TIMEOUT` (front).
