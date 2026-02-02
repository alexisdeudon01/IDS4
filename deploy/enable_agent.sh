#!/bin/bash

# Script pour installer et activer le service systemd de l'agent IDS2 SOC.

SERVICE_FILE="ids2-agent.service"
SERVICE_PATH="/etc/systemd/system/$SERVICE_FILE"
CURRENT_DIR="$(dirname "$(readlink -f "$0")")"

echo "Copie du fichier de service $SERVICE_FILE vers $SERVICE_PATH..."
sudo cp "$CURRENT_DIR/$SERVICE_FILE" "$SERVICE_PATH"

echo "Rechargement de la configuration systemd..."
sudo systemctl daemon-reload

echo "Activation du service ids2-agent..."
sudo systemctl enable ids2-agent.service

echo "Service ids2-agent activé. Il démarrera automatiquement au prochain redémarrage."
echo "Pour démarrer le service maintenant, exécutez : sudo deploy/start_agent.sh"
