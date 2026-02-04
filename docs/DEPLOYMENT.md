# 🚀 Guide de Déploiement Complet - Pipeline IDS

## Vue d'ensemble

Ce guide explique comment déployer concrètement tous les services du pipeline IDS sur un Raspberry Pi.

## Architecture de Déploiement

```
Machine de développement (votre PC)
         │
         │ SSH/SCP/RSYNC
         ▼
Raspberry Pi (capteur IDS)
         │
         ├─→ Suricata (service systemd)
         ├─→ Vector (service systemd)
         ├─→ Dashboard (service systemd)
         └─→ Configuration réseau (promiscuous)
```

## Prérequis

### Sur votre machine de développement

- SSH configuré avec clés
- rsync installé
- Accès réseau au Raspberry Pi

### Sur le Raspberry Pi

- Raspberry Pi OS (Debian-based)
- Accès SSH activé
- Accès sudo (sans mot de passe recommandé)

## Déploiement Automatique (Recommandé)

### Option 1 : Script complet

```bash
# 1. Configurer les variables d'environnement
export PI_HOST=192.168.1.100  # IP du Raspberry Pi
export PI_USER=pi              # Utilisateur SSH
export PI_SSH_KEY=~/.ssh/id_rsa  # Clé SSH (optionnel)
export REMOTE_DIR=/opt/ids     # Répertoire de déploiement

# 2. Lancer le déploiement
chmod +x scripts/deploy_pipeline.sh
./scripts/deploy_pipeline.sh
```

Le script effectue automatiquement :
1. ✅ Vérification de la connectivité SSH
2. ✅ Installation des dépendances système
3. ✅ Installation de Suricata
4. ✅ Installation de Vector
5. ✅ Configuration réseau (promiscuous mode)
6. ✅ Déploiement du code Python
7. ✅ Configuration de l'environnement Python
8. ✅ Configuration des services systemd
9. ✅ Démarrage des services
10. ✅ Vérification du déploiement

## Déploiement Manuel (Étape par étape)

### Étape 1 : Préparation du Raspberry Pi

```bash
# Se connecter au Pi
ssh pi@192.168.1.100

# Mettre à jour le système
sudo apt-get update && sudo apt-get upgrade -y

# Installer les dépendances de base
sudo apt-get install -y python3 python3-pip python3-venv curl wget git
```

### Étape 2 : Installation de Suricata

```bash
# Sur le Pi
sudo apt-get install -y suricata suricata-update

# Mettre à jour les règles
sudo suricata-update

# Créer les répertoires de logs
sudo mkdir -p /var/log/suricata
sudo chown suricata:suricata /var/log/suricata
```

**Configuration Suricata** (`/etc/suricata/suricata.yaml`) :

```yaml
af-packet:
  - interface: eth0
    cluster-id: 99
    cluster-type: cluster_flow
    defrag: yes

eve-log:
  enabled: yes
  filetype: regular
  filename: /var/log/suricata/eve.json
  types:
    - alert
    - http
    - dns
    - tls
```

### Étape 3 : Installation de Vector

```bash
# Sur le Pi
curl -1sLf 'https://repositories.timber.io/public/vector/gpg.8B2B0B5C5B5C5B5C.key' | \
  sudo gpg --dearmor -o /usr/share/keyrings/timber-vector-keyring.gpg

echo "deb [signed-by=/usr/share/keyrings/timber-vector-keyring.gpg] \
  https://repositories.timber.io/public/vector/deb/ubuntu jammy main" | \
  sudo tee /etc/apt/sources.list.d/timber-vector.list

sudo apt-get update
sudo apt-get install -y vector
```

**Configuration Vector** (`/etc/vector/vector.toml`) :

```toml
[sources.suricata]
type = "file"
include = ["/var/log/suricata/eve.json"]
read_from = "end"

[transforms.parse_json]
type = "remap"
inputs = ["suricata"]
source = '''
. = parse_json!(.message)
'''

[sinks.opensearch]
type = "elasticsearch"
inputs = ["parse_json"]
endpoint = "https://search-ids-domain-xxx.us-east-1.es.amazonaws.com"
index = "suricata-%Y.%m.%d"
auth.strategy = "basic"
auth.user = "${OPENSEARCH_USERNAME}"
auth.password = "${OPENSEARCH_PASSWORD}"
```

### Étape 4 : Configuration Réseau

```bash
# Sur le Pi - Activer le mode promiscuous
sudo ip link set eth0 promisc on

# Créer un service systemd pour persistance
sudo tee /etc/systemd/system/network-promiscuous.service > /dev/null << 'EOF'
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

sudo systemctl daemon-reload
sudo systemctl enable network-promiscuous.service
sudo systemctl start network-promiscuous.service
```

### Étape 5 : Déploiement du Code Python

```bash
# Depuis votre machine de développement
export PI_HOST=192.168.1.100
export PI_USER=pi
export REMOTE_DIR=/opt/ids

# Créer le répertoire sur le Pi
ssh ${PI_USER}@${PI_HOST} "mkdir -p ${REMOTE_DIR}"

# Synchroniser le code
rsync -avz --delete \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude '.venv' \
  --exclude '.git' \
  ./src/ ${PI_USER}@${PI_HOST}:${REMOTE_DIR}/src/

# Copier les fichiers de configuration
scp requirements.txt ${PI_USER}@${PI_HOST}:${REMOTE_DIR}/
scp config.yaml ${PI_USER}@${PI_HOST}:${REMOTE_DIR}/
scp secret.json ${PI_USER}@${PI_HOST}:${REMOTE_DIR}/  # Si existe
```

### Étape 6 : Configuration de l'Environnement Python

```bash
# Sur le Pi
cd /opt/ids

# Créer l'environnement virtuel
python3 -m venv .venv

# Activer et installer les dépendances
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Étape 7 : Configuration des Services systemd

**Service Suricata** (`/etc/systemd/system/suricata.service`) :

```ini
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
```

**Service Vector** (`/etc/systemd/system/vector.service`) :

```ini
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
```

**Service Dashboard** (`/etc/systemd/system/ids-dashboard.service`) :

```ini
[Unit]
Description=IDS Dashboard
After=network.target
Requires=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/opt/ids
Environment="PATH=/opt/ids/.venv/bin"
ExecStart=/opt/ids/.venv/bin/python -m ids.dashboard.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Activation des services** :

```bash
# Sur le Pi
sudo systemctl daemon-reload
sudo systemctl enable suricata vector ids-dashboard
sudo systemctl start suricata
sudo systemctl start vector
sudo systemctl start ids-dashboard
```

### Étape 8 : Configuration de l'Infrastructure

```bash
# Sur le Pi
cd /opt/ids
source .venv/bin/activate

# Configurer Tailnet et OpenSearch
python scripts/configure_infrastructure.py
```

Ou via les variables d'environnement :

```bash
# Créer .env sur le Pi
cat > /opt/ids/.env << EOF
DASHBOARD_PORT=8080
MIRROR_INTERFACE=eth0
LED_PIN=17

ELASTICSEARCH_HOSTS=https://search-ids-domain-xxx.us-east-1.es.amazonaws.com
ELASTICSEARCH_USERNAME=admin
ELASTICSEARCH_PASSWORD=your-password

TAILSCALE_TAILNET=your-tailnet
TAILSCALE_API_KEY=tskey-...

ANTHROPIC_API_KEY=sk-...
EOF
```

## Vérification du Déploiement

### Vérifier les services

```bash
# Sur le Pi
sudo systemctl status suricata
sudo systemctl status vector
sudo systemctl status ids-dashboard
```

### Vérifier les logs

```bash
# Logs Suricata
sudo journalctl -u suricata -f

# Logs Vector
sudo journalctl -u vector -f

# Logs Dashboard
sudo journalctl -u ids-dashboard -f

# Logs Suricata (fichier)
sudo tail -f /var/log/suricata/eve.json
```

### Vérifier le pipeline

```bash
# Depuis votre machine ou le Pi
curl http://192.168.1.100:8080/api/pipeline/status
curl http://192.168.1.100:8080/api/health
curl http://192.168.1.100:8080/api/alerts/recent
```

### Vérifier le trafic réseau

```bash
# Sur le Pi - Vérifier que eth0 reçoit du trafic
sudo tcpdump -i eth0 -c 10

# Vérifier le mode promiscuous
ip link show eth0 | grep PROMISC
```

## Mise à Jour

### Mise à jour du code

```bash
# Depuis votre machine de développement
./scripts/deploy_pipeline.sh  # Relance le déploiement
```

Ou manuellement :

```bash
rsync -avz --delete \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude '.venv' \
  ./src/ ${PI_USER}@${PI_HOST}:${REMOTE_DIR}/src/

ssh ${PI_USER}@${PI_HOST} "cd ${REMOTE_DIR} && \
  source .venv/bin/activate && \
  pip install -r requirements.txt && \
  sudo systemctl restart ids-dashboard"
```

### Mise à jour des règles Suricata

```bash
# Sur le Pi
sudo suricata-update
sudo systemctl restart suricata
```

## Résolution de Problèmes

### Suricata ne démarre pas

```bash
# Vérifier les logs
sudo journalctl -u suricata -n 50

# Vérifier la configuration
sudo suricata -c /etc/suricata/suricata.yaml --check-config

# Vérifier les permissions
sudo chown -R suricata:suricata /var/log/suricata
```

### Vector ne collecte pas les logs

```bash
# Vérifier la configuration
sudo vector validate --config /etc/vector/vector.toml

# Vérifier les permissions de lecture
sudo ls -la /var/log/suricata/eve.json

# Tester Vector manuellement
sudo vector --config /etc/vector/vector.toml --dry-run
```

### Dashboard inaccessible

```bash
# Vérifier que le service tourne
sudo systemctl status ids-dashboard

# Vérifier le port
sudo netstat -tlnp | grep 8080

# Vérifier les logs
sudo journalctl -u ids-dashboard -n 50
```

### Pas de trafic sur eth0

```bash
# Vérifier le mode promiscuous
ip link show eth0 | grep PROMISC

# Réactiver si nécessaire
sudo ip link set eth0 promisc on

# Vérifier la configuration du switch (port mirroring)
```

## Commandes Utiles

```bash
# Redémarrer tous les services
sudo systemctl restart suricata vector ids-dashboard

# Arrêter tous les services
sudo systemctl stop suricata vector ids-dashboard

# Voir les métriques système
curl http://localhost:8080/api/system/health

# Voir les stats réseau
curl http://localhost:8080/api/network/stats

# Voir les alertes récentes
curl http://localhost:8080/api/alerts/recent?limit=10
```

## Sécurité

- ✅ Services tournent avec les utilisateurs appropriés (suricata, pi)
- ✅ Logs dans `/var/log/` avec permissions correctes
- ✅ Dashboard accessible uniquement sur le réseau local (configurer un reverse proxy pour l'exposition)
- ✅ Clés API stockées dans `.env` (ne pas commiter dans git)

## Performance

- **Suricata** : Peut traiter ~1 Gbps sur un Pi 4
- **Vector** : Très léger, < 50 MB RAM
- **Dashboard** : < 100 MB RAM
- **Total** : ~200-300 MB RAM utilisée

## Prochaines Étapes

1. Configurer le port mirroring sur le switch TP-Link
2. Vérifier que le trafic arrive sur eth0
3. Configurer OpenSearch/Elasticsearch
4. Configurer Tailscale tailnet
5. Accéder au dashboard et vérifier les alertes
