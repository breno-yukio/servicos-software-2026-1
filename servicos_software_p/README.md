# Sistema de Transcrição de Áudio com API REST

## Visão do Projeto
Este projeto consiste em uma aplicação distribuída utilizando *frontend e backend em containers Docker*, que permite a transcrição de áudio para texto.

O sistema utiliza uma arquitetura baseada em *API REST*, onde o frontend envia um arquivo de áudio para o backend, que realiza o processamento e retorna o texto transcrito.

---

## Arquitetura

O sistema é composto por dois serviços principais:

- *Frontend:* Interface web desenvolvida com Gradio
- *Backend:* API REST desenvolvida com FastAPI
- *Modelo:* Whisper (transcrição de áudio)

---

## Fluxo do Sistema

1. O usuário acessa a interface web (Gradio)
2. Envia ou grava um áudio
3. O frontend envia o arquivo para o backend via HTTP
4. O backend processa o áudio utilizando o modelo Whisper
5. O backend retorna a transcrição em JSON
6. O frontend exibe o resultado na tela

---

## Tecnologias Utilizadas

- Python
- FastAPI
- Gradio
- Whisper
- Docker
- Docker Compose

---

## 🚀 Como Executar (Docker Compose)

Na pasta do projeto, execute:

```bash
docker compose up --build
