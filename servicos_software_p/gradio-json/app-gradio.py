import os
from pathlib import Path

import gradio as gr
import requests

# Na rede do Docker Compose: http://backend-json:8080
# Rodando o Gradio no host: BACKEND_URL=http://127.0.0.1:8080
BACKEND_URL = os.environ.get("BACKEND_URL", "http://backend-json:8080").rstrip("/")
TRANSCRICAO_TIMEOUT = int(os.environ.get("TRANSCRICAO_TIMEOUT", "600"))


def processa_audio(audio_path):
    if audio_path is None:
        return "Nenhum áudio recebido."

    path = Path(audio_path)
    mime = "audio/wav"
    if path.suffix.lower() in (".mp3", ".mpeg"):
        mime = "audio/mpeg"
    elif path.suffix.lower() == ".webm":
        mime = "audio/webm"
    elif path.suffix.lower() == ".ogg":
        mime = "audio/ogg"

    with open(audio_path, "rb") as f:
        files = {"file": (path.name or "audio.wav", f, mime)}
        url = f"{BACKEND_URL}/transcrever"
        try:
            response = requests.post(url, files=files, timeout=TRANSCRICAO_TIMEOUT)
            if response.status_code == 200:
                return response.json().get("texto", "Erro ao extrair texto.")
            detail = ""
            try:
                detail = response.json().get("detail", str(response.text))
            except Exception:
                detail = response.text or ""
            return f"Erro no servidor ({response.status_code}): {detail}"
        except requests.RequestException as e:
            return f"Erro de conexão com o backend ({url}): {str(e)}"


# Interface atualizada para entrada de Áudio
demo = gr.Interface(
    fn=processa_audio,
    inputs=gr.Audio(type="filepath", label="Grave sua voz ou envie um áudio"),
    outputs=gr.Textbox(label="Texto Transcrito (Prompt para IA)"),
    title="🎙️ Assistente de Voz para IA",
    description="Grave seu áudio. O Gradio enviará para o Backend via API, que converterá para texto usando IA.",
)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
