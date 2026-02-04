#!/bin/bash
# Déploiement rapide - Met à jour uniquement le code Python

set -e

PI_HOST="${PI_HOST:-192.168.1.100}"
PI_USER="${PI_USER:-pi}"
REMOTE_DIR="${REMOTE_DIR:-/opt/ids}"

SSH_OPTS=(-o StrictHostKeyChecking=accept-new -o ConnectTimeout=10)
SSH_CMD="ssh ${SSH_OPTS[*]} ${PI_USER}@${PI_HOST}"

echo "🚀 Déploiement rapide vers ${PI_USER}@${PI_HOST}"

# Synchroniser le code
echo "📦 Synchronisation du code..."
rsync -avz --delete \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude '.venv' \
  --exclude '.git' \
  -e "ssh ${SSH_OPTS[*]}" \
  ./src/ ${PI_USER}@${PI_HOST}:${REMOTE_DIR}/src/

# Mettre à jour les dépendances
echo "📦 Mise à jour des dépendances..."
$SSH_CMD "cd ${REMOTE_DIR} && \
  source .venv/bin/activate && \
  pip install -r requirements.txt"

# Redémarrer le dashboard
echo "🔄 Redémarrage du dashboard..."
$SSH_CMD "sudo systemctl restart ids-dashboard"

echo "✅ Déploiement rapide terminé!"
