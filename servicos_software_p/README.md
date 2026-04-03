**Criando uma estrutura para upload de arquivos**

Vamos criar uma estrutura com os seguintes componentes:

    - Um container para um app gradio-visao que irá apresentar a interface para a seleção de um arquivo de imagem para upload
    - Um container api-visao que será responsável por receber o nosso arquivo, reconhecer o seu conteúdo e armazená-lo em nosso serviço de armazenamento
    - Um container api-armazenamento que irá salvar o arquivo em um volume compartilhado e gravar o registro em um banco de dados SQLite.

Passo-a-passo
Vamos criar uma pasta para cada container:
 - gradio-visao
 - api-visao
 - api-armazenamento

Os conteúdos serão desenvolvidos durante a aula e ficarão disponibilizados em nosso repositório github.

**Gradio Visão**
Dentro do primeiro container, iremos criar os seguintes arquivos:

- Dockerfile
- app.py
- requirements.txt

Utilizar o código disponível em servicos_software_p/gradio-visao como modelos destes arquivos.

**API VISÃO**

Dentro do container api-visão, iremos criar os seguintes arquivos:
- Dockerfile
- main.py
- requirements.txt

Utilizar o código disponível em servicos_software_p/api-visao como modelos destes arquivos.

**API ARMAZENAMENTO**

- Dockerfile
- main.py
- requirements.txt

**Alteração no arquivo compose.yaml para habilitar os novos containers**

Devem ser acrescentadas as seguintes linhas no arquivo: 

```xml
  gradio-visao:
    build:
      context: gradio-visao
      dockerfile: Dockerfile
    ports:
      - "7861:7861"
    depends_on:
      - api-visao

  api-visao:
    build:
      context: api-visao
      dockerfile: Dockerfile
    ports:
      - "8081:8081"
    depends_on:
      - api-armazenamento

api-armazenamento:
  build:
    context: api-armazenamento
    dockerfile: Dockerfile
  ports:
    - "8082:8082"
  volumes:
    - dados-imagens:/dados

volumes:
  dados-imagens:

```

```sh
docker compose up -d --build

