#!/bin/bash

# Script pour arrêter proprement le service systemd de l'agent IDS2 SOC.

echo "Arrêt du service ids2-agent..."
sudo systemctl stop ids2-agent.service

echo "Service ids2-agent arrêté."
