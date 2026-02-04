#!/bin/bash
# Script de déploiement complet du pipeline IDS sur Raspberry Pi
# Installe et configure: Suricata, Vector, OpenSearch, Dashboard

set -e

# Configuration
PI_USER="${PI_USER:-pi}"
PI_HOST="${PI_HOST:-}"
PI_SSH_KEY="${PI_SSH_KEY:-}"
REMOTE_DIR="${REMOTE_DIR:-/opt/ids}"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo_info() {
    echo -e "${GREEN}ℹ️  $1${NC}"
}

echo_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

echo_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Vérifier les paramètres
if [ -z "$PI_HOST" ]; then
    echo_error "PI_HOST non défini. Utilisez: export PI_HOST=192.168.1.100"
    exit 1
fi

SSH_OPTS=(-o StrictHostKeyChecking=accept-new -o ConnectTimeout=10)
if [ -n "$PI_SSH_KEY" ]; then
    SSH_OPTS+=(-i "$PI_SSH_KEY")
fi

SSH_CMD="ssh ${SSH_OPTS[*]} ${PI_USER}@${PI_HOST}"
SCP_CMD="scp ${SSH_OPTS[*]}"

# ============================================================================
# ÉTAPE 1: Vérification de la connectivité
# ============================================================================
check_connectivity() {
    echo_info "Vérification de la connectivité SSH..."
    if ! $SSH_CMD "echo 'SSH OK'" > /dev/null 2>&1; then
        echo_error "Impossible de se connecter au Pi via SSH"
        echo "Vérifiez: PI_HOST, PI_USER, clés SSH"
        exit 1
    fi
    echo_info "✓ Connectivité SSH OK"
}

# ============================================================================
# ÉTAPE 2: Installation des dépendances système
# ============================================================================
install_system_deps() {
    echo_info "Installation des dépendances système sur le Pi..."
    
    $SSH_CMD "sudo bash -s" << 'INSTALL_DEPS'
set -e
export DEBIAN_FRONTEND=noninteractive

echo "Mise à jour du système..."
apt-get update

echo "Installation des paquets de base..."
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    wget \
    git \
    build-essential \
    libpcap-dev \
    libyaml-dev \
    libjansson-dev \
    libmagic-dev \
    libcap-ng-dev \
    libnet1-dev \
    libnetfilter-queue-dev \
    libnfnetlink-dev \
    libnss3-dev \
    libgeoip-dev \
    liblua5.1-dev \
    libhiredis-dev \
    libevent-dev \
    pkg-config \
    rustc \
    cargo

echo "✓ Dépendances système installées"
INSTALL_DEPS

    echo_info "✓ Dépendances système installées"
}

# ============================================================================
# ÉTAPE 3: Installation de Suricata
# ============================================================================
install_suricata() {
    echo_info "Installation et configuration de Suricata..."
    
    $SSH_CMD "sudo bash -s" << 'INSTALL_SURICATA'
set -e

# Installer Suricata depuis les repos Debian
if ! command -v suricata &> /dev/null; then
    echo "Installation de Suricata..."
    apt-get install -y suricata suricata-update
fi

# Mettre à jour les règles
echo "Mise à jour des règles Suricata..."
suricata-update

# Créer les répertoires de logs
mkdir -p /var/log/suricata
chown suricata:suricata /var/log/suricata

# Configuration de base de Suricata
if [ ! -f /etc/suricata/suricata.yaml.backup ]; then
    cp /etc/suricata/suricata.yaml /etc/suricata/suricata.yaml.backup
fi

echo "✓ Suricata installé"
INSTALL_SURICATA

    # Copier la configuration Suricata personnalisée
    if [ -f "suricata/suricata.yaml" ]; then
        echo_info "Copie de la configuration Suricata..."
        $SCP_CMD suricata/suricata.yaml ${PI_USER}@${PI_HOST}:/tmp/suricata.yaml
        $SSH_CMD "sudo cp /tmp/suricata.yaml /etc/suricata/suricata.yaml && sudo chown root:root /etc/suricata/suricata.yaml"
    fi

    echo_info "✓ Suricata configuré"
}

# ============================================================================
# ÉTAPE 4: Installation de Vector
# ============================================================================
install_vector() {
    echo_info "Installation de Vector..."
    
    $SSH_CMD "bash -s" << 'INSTALL_VECTOR'
set -e

# Installer Vector via le script officiel
if ! command -v vector &> /dev/null; then
    echo "Téléchargement et installation de Vector..."
    curl -1sLf 'https://repositories.timber.io/public/vector/gpg.8B2B0B5C5B5C5B5C.key' | gpg --dearmor | sudo tee /usr/share/keyrings/timber-vector-keyring.gpg > /dev/null
    echo "deb [signed-by=/usr/share/keyrings/timber-vector-keyring.gpg] https://repositories.timber.io/public/vector/deb/ubuntu jammy main" | sudo tee /etc/apt/sources.list.d/timber-vector.list
    sudo apt-get update
    sudo apt-get install -y vector
fi

echo "✓ Vector installé"
INSTALL_VECTOR

    # Copier la configuration Vector
    if [ -f "vector/vector.toml" ]; then
        echo_info "Copie de la configuration Vector..."
        $SCP_CMD vector/vector.toml ${PI_USER}@${PI_HOST}:/tmp/vector.toml
        $SSH_CMD "sudo mkdir -p /etc/vector && sudo cp /tmp/vector.toml /etc/vector/vector.toml && sudo chown root:root /etc/vector/vector.toml"
    fi

    echo_info "✓ Vector configuré"
}

# ============================================================================
# ÉTAPE 5: Configuration réseau (Promiscuous mode)
# ============================================================================
configure_network() {
    echo_info "Configuration de l'interface réseau (promiscuous mode)..."
    
    $SSH_CMD "sudo bash -s" << 'CONFIG_NETWORK'
set -e

# Activer le mode promiscuous sur eth0
ip link set eth0 promisc on

# Créer un service systemd pour activer au démarrage
cat > /etc/systemd/system/network-promiscuous.service << 'EOF'
[Unit]
Description=Enable promiscuous mode on eth0
After=network-pre.target
Before=network.target

[Service]
Type=oneshot
ExecStart=/bin/ip link set eth0 promisc on
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable network-promiscuous.service

echo "✓ Interface réseau configurée"
CONFIG_NETWORK

    echo_info "✓ Mode promiscuous activé"
}

# ============================================================================
# ÉTAPE 6: Déploiement du code Python
# ============================================================================
deploy_python_code() {
    echo_info "Déploiement du code Python sur le Pi..."
    
    # Créer le répertoire distant
    $SSH_CMD "mkdir -p ${REMOTE_DIR}"
    
    # Synchroniser les fichiers
    echo_info "Synchronisation des fichiers..."
    rsync -avz --delete \
        --exclude '__pycache__' \
        --exclude '*.pyc' \
        --exclude '.venv' \
        --exclude '.git' \
        --exclude 'dist' \
        --exclude 'htmlcov' \
        -e "ssh ${SSH_OPTS[*]}" \
        ./src/ ${PI_USER}@${PI_HOST}:${REMOTE_DIR}/src/
    
    # Copier les fichiers de configuration
    $SCP_CMD requirements.txt ${PI_USER}@${PI_HOST}:${REMOTE_DIR}/
    $SCP_CMD pyproject.toml ${PI_USER}@${PI_HOST}:${REMOTE_DIR}/ 2>/dev/null || true
    $SCP_CMD config.yaml ${PI_USER}@${PI_HOST}:${REMOTE_DIR}/ 2>/dev/null || true
    if [ -f "secret.json" ]; then
        $SCP_CMD secret.json ${PI_USER}@${PI_HOST}:${REMOTE_DIR}/ 2>/dev/null || true
    fi
    
    echo_info "✓ Code Python déployé"
}

# ============================================================================
# ÉTAPE 7: Installation de l'environnement Python
# ============================================================================
setup_python_env() {
    echo_info "Configuration de l'environnement Python..."
    
    $SSH_CMD "bash -s" << SETUP_PYTHON
set -e
cd ${REMOTE_DIR}

# Créer l'environnement virtuel
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

# Activer et installer les dépendances
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "✓ Environnement Python configuré"
SETUP_PYTHON

    echo_info "✓ Environnement Python configuré"
}

# ============================================================================
# ÉTAPE 8: Configuration des services systemd
# ============================================================================
setup_systemd_services() {
    echo_info "Configuration des services systemd..."
    
    $SSH_CMD "sudo bash -s" << SETUP_SERVICES
set -e
cd ${REMOTE_DIR}

# Service Suricata
cat > /etc/systemd/system/suricata.service << 'EOF'
[Unit]
Description=Suricata IDS
After=network.target network-promiscuous.service
Wants=network-promiscuous.service

[Service]
Type=simple
User=suricata
Group=suricata
ExecStart=/usr/bin/suricata -c /etc/suricata/suricata.yaml -i eth0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Service Vector
cat > /etc/systemd/system/vector.service << 'EOF'
[Unit]
Description=Vector Log Collector
After=network.target suricata.service
Requires=suricata.service

[Service]
Type=simple
ExecStart=/usr/bin/vector --config /etc/vector/vector.toml
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Service Dashboard
cat > /etc/systemd/system/ids-dashboard.service << 'EOF'
[Unit]
Description=IDS Dashboard
After=network.target
Requires=network.target

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
EOF

systemctl daemon-reload

echo "✓ Services systemd configurés"
SETUP_SERVICES

    echo_info "✓ Services systemd configurés"
}

# ============================================================================
# ÉTAPE 9: Configuration de l'infrastructure (Tailnet + OpenSearch)
# ============================================================================
configure_infrastructure() {
    echo_info "Configuration de l'infrastructure (Tailnet + OpenSearch)..."
    
    echo_warn "Cette étape nécessite des clés API. Configurez-les dans .env sur le Pi"
    echo_info "Pour configurer manuellement:"
    echo "  ssh ${PI_USER}@${PI_HOST}"
    echo "  cd ${REMOTE_DIR}"
    echo "  source .venv/bin/activate"
    echo "  python scripts/configure_infrastructure.py"
}

# ============================================================================
# ÉTAPE 10: Démarrage des services
# ============================================================================
start_services() {
    echo_info "Démarrage des services..."
    
    $SSH_CMD "sudo bash -s" << START_SERVICES
set -e

# Activer les services
systemctl enable network-promiscuous.service
systemctl enable suricata.service
systemctl enable vector.service
systemctl enable ids-dashboard.service

# Démarrer les services
systemctl start network-promiscuous.service
systemctl start suricata.service
sleep 5
systemctl start vector.service
sleep 5
systemctl start ids-dashboard.service

echo "✓ Services démarrés"
START_SERVICES

    echo_info "✓ Services démarrés"
}

# ============================================================================
# ÉTAPE 11: Vérification
# ============================================================================
verify_deployment() {
    echo_info "Vérification du déploiement..."
    
    echo_info "Vérification des services:"
    $SSH_CMD "sudo systemctl is-active suricata vector ids-dashboard" || echo_warn "Certains services ne sont pas actifs"
    
    echo_info "Vérification des logs Suricata:"
    $SSH_CMD "sudo tail -n 5 /var/log/suricata/eve.json" 2>/dev/null || echo_warn "Aucun log Suricata trouvé"
    
    echo_info "Vérification du dashboard:"
    $SSH_CMD "curl -s http://localhost:8080/api/health" || echo_warn "Dashboard non accessible"
    
    echo_info "✓ Vérification terminée"
}

# ============================================================================
# FONCTION PRINCIPALE
# ============================================================================
main() {
    echo "🚀 Déploiement complet du pipeline IDS sur Raspberry Pi"
    echo "Pi: ${PI_USER}@${PI_HOST}"
    echo "Répertoire: ${REMOTE_DIR}"
    echo ""
    
    check_connectivity
    install_system_deps
    install_suricata
    install_vector
    configure_network
    deploy_python_code
    setup_python_env
    setup_systemd_services
    configure_infrastructure
    start_services
    verify_deployment
    
    echo ""
    echo_info "✨ Déploiement terminé avec succès!"
    echo ""
    echo "Commandes utiles:"
    echo "  # Voir les logs"
    echo "  ssh ${PI_USER}@${PI_HOST} 'sudo journalctl -u suricata -f'"
    echo "  ssh ${PI_USER}@${PI_HOST} 'sudo journalctl -u vector -f'"
    echo "  ssh ${PI_USER}@${PI_HOST} 'sudo journalctl -u ids-dashboard -f'"
    echo ""
    echo "  # Accéder au dashboard"
    echo "  http://${PI_HOST}:8080"
    echo ""
    echo "  # Vérifier le statut"
    echo "  ssh ${PI_USER}@${PI_HOST} 'curl http://localhost:8080/api/pipeline/status'"
}

# Exécution
main "$@"
