#!/usr/bin/env bash
# Sobe o dashboard com Podman puro (pod + container).
# Uso:
#   ./podman-run.sh build    # constrói a imagem
#   ./podman-run.sh up       # cria o pod e sobe o container
#   ./podman-run.sh down     # remove o pod
#   ./podman-run.sh logs     # acompanha os logs
set -euo pipefail

IMAGE="job-scraper-dashboard:latest"
POD="job-scraper"
CONTAINER="job-scraper-dashboard"
VOLUME="jobs-data"
PORT="${PORT:-8000}"

# Variáveis de ambiente do Telegram (opcionais) — leia do .env se existir
TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
TELEGRAM_CHAT_ID="${TELEGRAM_CHAT_ID:-}"
if [[ -f .env ]]; then
  # shellcheck disable=SC1091
  set -a; source .env; set +a
fi

build() {
  podman build -t "$IMAGE" -f Dockerfile .
}

up() {
  podman volume exists "$VOLUME" || podman volume create "$VOLUME"

  # (Re)cria o pod, publicando a porta no nível do pod
  podman pod exists "$POD" && podman pod rm -f "$POD"
  podman pod create --name "$POD" -p "${PORT}:8000"

  podman run -d --pod "$POD" --name "$CONTAINER" \
    -e DATABASE_PATH=/data/jobs.db \
    -e TELEGRAM_BOT_TOKEN="$TELEGRAM_BOT_TOKEN" \
    -e TELEGRAM_CHAT_ID="$TELEGRAM_CHAT_ID" \
    -v "${VOLUME}:/data" \
    --restart unless-stopped \
    "$IMAGE"

  echo "Dashboard em http://localhost:${PORT}"
}

down() {
  podman pod rm -f "$POD" 2>/dev/null || true
}

logs() {
  podman logs -f "$CONTAINER"
}

case "${1:-up}" in
  build) build ;;
  up)    up ;;
  down)  down ;;
  logs)  logs ;;
  *) echo "Uso: $0 {build|up|down|logs}"; exit 1 ;;
esac
