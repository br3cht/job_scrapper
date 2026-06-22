# Job Scraper

CLI para buscar vagas de emprego remotas em múltiplas plataformas.

## Instalação

```bash
cd job_scraper
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou venv\Scripts\activate  # Windows
pip install -r requirements.txt
playwright install
```

## Configuração

Copie `.env.example` para `.env` e configure:

```bash
TELEGRAM_BOT_TOKEN=seu_token
TELEGRAM_CHAT_ID=seu_chat_id
```

## Uso

```bash
python main.py search "python developer"           # Buscar vagas
python main.py list                                # Listar vagas não enviadas
python main.py list --all                          # Listar todas as vagas
python main.py list --markdown vagas.md            # Gerar arquivo Markdown com vagas não enviadas
python main.py list --all --markdown vagas.md      # Gerar arquivo Markdown com todas as vagas
python main.py send                                # Enviar para Telegram
python main.py count                               # Contar vagas no banco
python main.py clear                               # Limpar banco
```

### Opções do list

```bash
--all/--unsent             # Todas as vagas ou apenas não enviadas
--markdown, -m arquivo.md  # Salvar as vagas listadas em Markdown
```

### Opções do search

```bash
--sites indeed,remoteok,weworkremotely,wellfound  # Sites específicos
--remote/--no-remote                              # Apenas remotas (padrão: true)
--indeed-region br|world                          # Região do Indeed (padrão: br)
```

## Dashboard web

Aplicação web (FastAPI) para visualizar e gerenciar as vagas pelo navegador:
visualizar/filtrar vagas, estatísticas por fonte, disparar uma nova busca e
enviar para o Telegram — tudo sem usar a CLI.

### Rodar localmente

```bash
python main.py serve                 # http://localhost:8000
python main.py serve --port 9000     # porta customizada
python main.py serve --reload        # modo desenvolvimento (auto-reload)
```

### Rodar com Podman (pod)

A imagem já inclui o Chromium headless usado pelos scrapers.

```bash
./podman-run.sh build    # constrói a imagem
./podman-run.sh up       # cria o pod e sobe o container -> http://localhost:8000
./podman-run.sh logs     # acompanha os logs
./podman-run.sh down     # remove o pod
```

O banco `jobs.db` é persistido no volume Podman `jobs-data` (montado em `/data`).
Para mudar a porta: `PORT=9000 ./podman-run.sh up`.

Para habilitar o envio ao Telegram pelo dashboard, defina `TELEGRAM_BOT_TOKEN` e
`TELEGRAM_CHAT_ID` (no `.env` ou como variáveis de ambiente) antes do `up`.

> Também há um `compose.yml` para quem preferir `podman compose up -d`.

## Plataformas suportadas

- Indeed
- RemoteOK
- WeWorkRemotely
- Wellfound
