import os
import shutil
import tempfile
from pathlib import Path

import whisper
from fastapi import FastAPI, File, HTTPException, UploadFile

WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "base")

app = FastAPI()

print(f"Carregando modelo de IA (Whisper: {WHISPER_MODEL})...")
model = whisper.load_model(WHISPER_MODEL)
print("Modelo carregado!")


@app.get("/")
def diz_ola():
    return {"Olá": "Mundo"}


@app.post("/transcrever")
async def transcrever_audio(file: UploadFile = File(...)):
    nome = file.filename or "audio.wav"
    sufixo = Path(nome).suffix or ".wav"
    caminho_temp = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=sufixo) as tmp:
            caminho_temp = tmp.name
            shutil.copyfileobj(file.file, tmp)
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"Falha ao salvar áudio: {e}") from e

    try:
        resultado = model.transcribe(caminho_temp, language="pt")
        texto = (resultado.get("text") or "").strip()
        return {"texto": texto}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na transcrição: {e}") from e
    finally:
        if caminho_temp and os.path.exists(caminho_temp):
            os.remove(caminho_temp)
