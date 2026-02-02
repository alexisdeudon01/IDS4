#!/bin/bash

# Script pour démarrer le service systemd de l'agent IDS2 SOC et afficher ses logs.

echo "Démarrage du service Suricata..."
sudo systemctl start suricata.service

echo "Démarrage de la pile Docker Compose..."
# Naviguer vers le répertoire docker et démarrer la pile
(cd docker && sudo docker compose up -d)

echo "Démarrage du service ids2-agent..."
sudo systemctl start ids2-agent.service

echo "Affichage des logs du service ids2-agent (Ctrl+C pour quitter)..."
sudo journalctl -f -u ids2-agent.service
