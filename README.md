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
python main.py send                                # Enviar para Telegram
python main.py count                               # Contar vagas no banco
python main.py clear                               # Limpar banco
```

### Opções do search

```bash
--sites indeed,remoteok,weworkremotely,wellfound  # Sites específicos
--remote/--no-remote                              # Apenas remotas (padrão: true)
--indeed-region br|world                          # Região do Indeed (padrão: br)
```

## Plataformas suportadas

- Indeed
- RemoteOK
- WeWorkRemotely
- Wellfound
