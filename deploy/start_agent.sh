#!/bin/bash

# Script pour démarrer le service systemd de l'agent IDS2 SOC et afficher ses logs.

echo "Démarrage du service ids2-agent..."
sudo systemctl start ids2-agent.service

echo "Affichage des logs du service ids2-agent (Ctrl+C pour quitter)..."
sudo journalctl -f -u ids2-agent.service
