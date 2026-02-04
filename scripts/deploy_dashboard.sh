#!/bin/bash
# Script simple de déploiement du Dashboard IDS
# Demande IP et mot de passe, upload et lance le dashboard

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo_info() { echo -e "${GREEN}ℹ️  $1${NC}"; }
echo_error() { echo -e "${RED}❌ $1${NC}"; }
echo_success() { echo -e "${GREEN}✅ $1${NC}"; }

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}🚀 Déploiement Dashboard IDS${NC}"
echo -e "${BLUE}========================================${NC}\n"

# 1. Demander les informations
read -p "IP du Raspberry Pi: " PI_IP
read -p "Utilisateur SSH (défaut: pi): " PI_USER
PI_USER=${PI_USER:-pi}
read -sp "Mot de passe SSH: " PI_PASS
echo ""
REMOTE_DIR="/opt/ids"

# 2. Vérifier dépendances locales
echo_info "Vérification des dépendances locales..."
command -v ssh >/dev/null || { echo_error "ssh non trouvé"; exit 1; }
command -v rsync >/dev/null || { echo_error "rsync non trouvé"; exit 1; }
command -v sshpass >/dev/null || echo_error "sshpass non installé (optionnel)"
echo_success "Dépendances locales OK"

# 3. Vérifier connectivité
echo_info "Vérification SSH..."
if command -v sshpass >/dev/null; then
    sshpass -p "$PI_PASS" ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=5 \
        "${PI_USER}@${PI_IP}" "echo 'OK'" >/dev/null 2>&1 || { echo_error "Connexion SSH échouée"; exit 1; }
else
    ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=5 \
        "${PI_USER}@${PI_IP}" "echo 'OK'" >/dev/null 2>&1 || { echo_error "Connexion SSH échouée"; exit 1; }
fi
echo_success "SSH OK"

# 4. Vérifier dépendances Pi
echo_info "Vérification dépendances Pi..."
if command -v sshpass >/dev/null; then
    sshpass -p "$PI_PASS" ssh "${PI_USER}@${PI_IP}" \
        "python3 --version && python3 -m venv --help >/dev/null 2>&1" >/dev/null 2>&1 || \
        { echo_error "Dépendances manquantes sur Pi"; exit 1; }
else
    ssh "${PI_USER}@${PI_IP}" \
        "python3 --version && python3 -m venv --help >/dev/null 2>&1" >/dev/null 2>&1 || \
        { echo_error "Dépendances manquantes sur Pi"; exit 1; }
fi
echo_success "Dépendances Pi OK"

# 5. Créer répertoire
echo_info "Création répertoire..."
if command -v sshpass >/dev/null; then
    sshpass -p "$PI_PASS" ssh "${PI_USER}@${PI_IP}" "mkdir -p ${REMOTE_DIR}"
else
    ssh "${PI_USER}@${PI_IP}" "mkdir -p ${REMOTE_DIR}"
fi

# 6. Upload dashboard
echo_info "Upload du dashboard..."
if command -v sshpass >/dev/null; then
    rsync -avz --delete --exclude '__pycache__' --exclude '*.pyc' --exclude '.venv' --exclude '.git' \
        -e "sshpass -p '$PI_PASS' ssh -o StrictHostKeyChecking=accept-new" \
        ./src/ids/dashboard/ "${PI_USER}@${PI_IP}:${REMOTE_DIR}/src/ids/dashboard/"
    [ -d "./frontend" ] && rsync -avz -e "sshpass -p '$PI_PASS' ssh -o StrictHostKeyChecking=accept-new" \
        ./frontend/ "${PI_USER}@${PI_IP}:${REMOTE_DIR}/frontend/"
    [ -f "./requirements.txt" ] && sshpass -p "$PI_PASS" scp -o StrictHostKeyChecking=accept-new \
        ./requirements.txt "${PI_USER}@${PI_IP}:${REMOTE_DIR}/"
else
    rsync -avz --delete --exclude '__pycache__' --exclude '*.pyc' --exclude '.venv' --exclude '.git' \
        -e "ssh -o StrictHostKeyChecking=accept-new" \
        ./src/ids/dashboard/ "${PI_USER}@${PI_IP}:${REMOTE_DIR}/src/ids/dashboard/"
    [ -d "./frontend" ] && rsync -avz -e "ssh -o StrictHostKeyChecking=accept-new" \
        ./frontend/ "${PI_USER}@${PI_IP}:${REMOTE_DIR}/frontend/"
    [ -f "./requirements.txt" ] && scp -o StrictHostKeyChecking=accept-new \
        ./requirements.txt "${PI_USER}@${PI_IP}:${REMOTE_DIR}/"
fi
echo_success "Dashboard uploadé"

# 7. Installer dépendances Python
echo_info "Installation dépendances Python..."
if command -v sshpass >/dev/null; then
    sshpass -p "$PI_PASS" ssh "${PI_USER}@${PI_IP}" << EOF
cd ${REMOTE_DIR}
[ ! -d ".venv" ] && python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
EOF
else
    ssh "${PI_USER}@${PI_IP}" << EOF
cd ${REMOTE_DIR}
[ ! -d ".venv" ] && python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
EOF
fi
echo_success "Dépendances installées"

# 8. Créer service systemd
echo_info "Création service systemd..."
if command -v sshpass >/dev/null; then
    sshpass -p "$PI_PASS" ssh -t "${PI_USER}@${PI_IP}" << EOF
sudo tee /etc/systemd/system/ids-dashboard.service > /dev/null << 'EOFSERVICE'
[Unit]
Description=IDS Dashboard
After=network.target

[Service]
Type=simple
User=${PI_USER}
WorkingDirectory=${REMOTE_DIR}
Environment="PATH=${REMOTE_DIR}/.venv/bin"
ExecStart=${REMOTE_DIR}/.venv/bin/python -m ids.dashboard.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOFSERVICE
sudo systemctl daemon-reload
sudo systemctl enable ids-dashboard.service
EOF
else
    ssh -t "${PI_USER}@${PI_IP}" << EOF
sudo tee /etc/systemd/system/ids-dashboard.service > /dev/null << 'EOFSERVICE'
[Unit]
Description=IDS Dashboard
After=network.target

[Service]
Type=simple
User=${PI_USER}
WorkingDirectory=${REMOTE_DIR}
Environment="PATH=${REMOTE_DIR}/.venv/bin"
ExecStart=${REMOTE_DIR}/.venv/bin/python -m ids.dashboard.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOFSERVICE
sudo systemctl daemon-reload
sudo systemctl enable ids-dashboard.service
EOF
fi
echo_success "Service créé"

# 9. Démarrer dashboard
echo_info "Démarrage dashboard..."
if command -v sshpass >/dev/null; then
    sshpass -p "$PI_PASS" ssh -t "${PI_USER}@${PI_IP}" "sudo systemctl start ids-dashboard"
else
    ssh -t "${PI_USER}@${PI_IP}" "sudo systemctl start ids-dashboard"
fi
sleep 3
echo_success "Dashboard démarré"

# 10. Vérifier
echo_info "Vérification..."
sleep 2
if curl -s "http://${PI_IP}:8080/api/health" >/dev/null 2>&1; then
    echo_success "Dashboard accessible sur http://${PI_IP}:8080"
else
    echo_error "Dashboard non accessible immédiatement"
    echo "Vérifiez: ssh ${PI_USER}@${PI_IP} 'sudo journalctl -u ids-dashboard -f'"
fi

echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}✨ Déploiement terminé!${NC}\n"
echo -e "Accédez: ${BLUE}http://${PI_IP}:8080${NC}\n"
echo -e "Configurez via l'interface web!"
echo -e "${BLUE}========================================${NC}\n"
