#!/bin/bash
# Deploy script for Meditacao Swarm
# Usage: bash deploy.sh
set -e

cd "$(dirname "$0")"

# Load environment variables
if [ -f /opt/stacks/meditacao/.env ]; then
    echo "Loading /opt/stacks/meditacao/.env"
    set -a
    source /opt/stacks/meditacao/.env
    set +a
else
    echo "ERROR: /opt/stacks/meditacao/.env not found!"
    echo "Copy .env.example to /opt/stacks/meditacao/.env and fill in values."
    exit 1
fi

# Verify required vars
for var in DEEPSEEK_API_KEY BASEROW_TOKEN TELEGRAM_BOT_TOKEN; do
    if [ -z "${!var}" ]; then
        echo "ERROR: $var is not set"
        exit 1
    fi
done

echo "Building image..."
docker build -t meditacao-swarm:latest .

echo "Deploying stack..."
docker stack deploy -c meditacao.yml meditacao

echo "Done! Check: docker service ps meditacao_meditacao"
