# Planejador de Rotina de Estudos

## Visão do Projeto

Este projeto consiste em criar um frontend e backend em containers Docker, que permite a geração automática de uma rotina de estudos personalizada.

A aplicação segue o modelo de arquitetura cliente-servidor com API REST, onde o frontend coleta as informações do usuário e envia para o backend, responsável por processar os dados e retornar um plano de estudos estruturado.

---

## Arquitetura

O sistema é composto por dois serviços principais:

* **Frontend:** Interface web responsável pela interação com o usuário
* **Backend:** API REST responsável pelo processamento e geração da rotina
* **Modelo:** Algoritmo baseado em regras de negócio

A comunicação entre frontend e backend ocorre via **HTTP (API REST)**.

---

## Fluxo do Sistema

1. O usuário acessa a interface web
2. Preenche os dados necessários:

   * dias disponíveis para estudo
   * horas de estudo por dia
   * objetivo (prova, revisão, aprendizado ou trabalho)
   * matérias e nível de dificuldade
   * período preferido (manhã, tarde ou noite)
   * horários já comprometidos

3. O frontend envia os dados para o backend via requisição HTTP (POST)
4. O backend processa as informações utilizando regras de negócio
5. Um plano de estudos é gerado e retornado em formato JSON
6. O frontend exibe a rotina organizada por dia

---

## Tecnologias Utilizadas

* Python
* FastAPI
* HTML / CSS / JavaScript
* Docker
* Docker Compose

---

## Regras de Negócio

O backend implementa um modelo próprio baseado em regras para gerar a rotina:

### Distribuição por dificuldade

* Baixa → peso 1
* Média → peso 2
* Alta → peso 3

Matérias com maior dificuldade recebem mais tempo de estudo.

---

### Divisão entre teoria e exercícios

Depende do objetivo do usuário:

* Prova → foco em exercícios
* Revisão → foco em exercício mas com teoria também
* Aprendizado → foco em teoria
* Trabalho → equilíbrio entre teoria e prática

---

### Períodos de estudo

* Manhã → 08:00 às 12:00
* Tarde → 13:00 às 18:00
* Noite → 19:00 às 22:30

---

### Restrições

* O sistema evita horários já ocupados pelo usuário
* Distribui as matérias ao longo dos dias
* Alterna conteúdos para evitar repetição excessiva

---
