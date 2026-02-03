# IDS Agent - Système de Détection d'Intrusion

Agent IDS distribué pour Raspberry Pi avec monitoring Tailscale mesh network.

## 🚀 Quick Start

### Prérequis
- Python 3.10+
- Raspberry Pi 5 (ou compatible)
- Compte Tailscale
- Compte AWS (optionnel)

### Installation

```bash
# Clone le projet
git clone https://github.com/alexisdeudon01/oi.git
cd oi

# Installe les dépendances
pip install -r requirements.txt

# Configure l'environnement
cp config.yaml.example config.yaml
# Édite config.yaml avec tes paramètres
```

## 📊 Monitoring Tailscale

### Génération du Network Health Map

```bash
# Mode interactif
python scripts/monitor_tailnet.py

# Depuis le code
from ids.monitoring import TailnetMonitor

monitor = TailnetMonitor(api_key="tskey-...", tailnet_name="yourname.github")
snapshot = monitor.get_current_state()
snapshot = monitor.measure_mesh_latency(snapshot)
monitor.generate_interactive_graph(snapshot)
```

### Fonctionnalités

- **Visualisation interactive** : graphe Pyvis avec tous les nœuds Tailscale
- **Mesure de latence** : ping automatique vers tous les nœuds online
- **Taille des nœuds** : proportionnelle à la latence (plus gros = plus rapide)
- **Liens vers console** : clic sur un nœud → console Tailscale
- **Snapshot temporel** : capture l'état du réseau à un instant T

## 🔐 Configuration des Secrets

### GitHub Codespaces

```bash
# Mode interactif (recommandé)
./scripts/gh_codespaces_set_secrets.sh --repo alexisdeudon01/oi

# Mode non-interactif
PI_IP="100.118.244.54" \
PI_USER="pi" \
TS_OAUTH_CLIENT_ID="..." \
TS_OAUTH_CLIENT_SECRET="..." \
TAILSCALE_TAILNET="yourname.github" \
TAILSCALE_API_KEY="tskey-..." \
AWS_ACCESS_KEY_ID="..." \
AWS_SECRET_ACCESS_KEY="..." \
AWS_REGION="eu-central-1" \
./scripts/gh_codespaces_set_secrets.sh --repo alexisdeudon01/oi
```

### Synchronisation vers GitHub Actions

```bash
./scripts/gh_actions_sync_secrets.sh --repo alexisdeudon01/oi
```

### Bootstrap complet (tout-en-un)

```bash
./scripts/gh_actions_bootstrap.sh --repo alexisdeudon01/oi
```

## 🔧 Secrets Requis

| Secret | Description | Exemple |
|--------|-------------|---------|
| `PI_IP` | IP Tailscale du Pi | `100.118.244.54` |
| `PI_USER` | User SSH du Pi | `pi` |
| `PI` | Clé SSH privée | (contenu de `~/.ssh/pi_github_actions`) |
| `TS_OAUTH_CLIENT_ID` | OAuth client ID Tailscale | `k...` |
| `TS_OAUTH_CLIENT_SECRET` | OAuth client secret | `tskey-client-...` |
| `TAILSCALE_TAILNET` | Nom du tailnet | `yourname.github` |
| `TAILSCALE_API_KEY` | API key Tailscale | `tskey-api-...` |
| `AWS_ACCESS_KEY_ID` | AWS access key | `AKIA...` |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | `...` |
| `AWS_REGION` | AWS region | `eu-central-1` |
| `AWS_SESSION_TOKEN` | AWS session token (optionnel) | `...` |

### Où récupérer les clés Tailscale

- **OAuth client** : https://login.tailscale.com/admin/oauth-clients
- **API key** : https://login.tailscale.com/admin/settings/keys
- **Tailnet name** : visible dans l'URL de ton admin Tailscale

## 🧪 Tests

```bash
# Tests unitaires
pytest tests/unit/ -v

# Tests d'intégration
pytest tests/integration/ -v

# Coverage
pytest --cov=src/ids --cov-report=html
```

## 🚢 Déploiement

### Via GitHub Actions (automatique)

Le workflow CI/CD se déclenche sur push vers `main` ou `dev` :

1. **Job connectivity** : vérifie Tailscale + AWS + génère le Network Health Map
2. **Job test** : tests unitaires + intégration
3. **Job code-quality** : linting (non bloquant)
4. **Job deploy** : déploiement sur le Pi via Tailscale

### Manuel

```bash
# Déploiement direct
./deploy/deploy_pi.sh 100.118.244.54

# Avec Tailscale
tailscale up --authkey=tskey-...
./deploy/deploy_pi.sh 100.118.244.54
```

## 📁 Structure du Projet

```
oi/
├── src/ids/
│   ├── monitoring/          # Monitoring Tailscale
│   │   ├── tailnet_monitor.py
│   │   └── __init__.py
│   ├── app/                 # Application layer
│   ├── composants/          # Components (Suricata, Vector, etc.)
│   ├── config/              # Configuration
│   ├── domain/              # Domain models
│   ├── infrastructure/      # Infrastructure (AWS, Redis, etc.)
│   └── interfaces/          # Interfaces/protocols
├── scripts/
│   ├── monitor_tailnet.py   # Script monitoring standalone
│   ├── gh_actions_bootstrap.sh
│   ├── gh_codespaces_set_secrets.sh
│   └── gh_actions_sync_secrets.sh
├── tests/
│   ├── unit/
│   └── integration/
├── .github/workflows/
│   └── ci-cd.yml
├── requirements.txt
└── config.yaml
```

## 🔍 Monitoring en Production

Le **Network Health Map** est généré automatiquement à chaque run du workflow CI/CD et disponible en artifact GitHub Actions pendant 7 jours.

### Accès au Health Map

1. Va dans **Actions** → dernier workflow run
2. Télécharge l'artifact `network-health-map`
3. Ouvre `network_health_map.html` dans un navigateur

### Interprétation

- **Nœud vert** : online
- **Nœud rouge** : offline
- **Taille du nœud** : inversement proportionnelle à la latence
- **Hover** : affiche les détails (OS, IP, latency, tags)
- **Clic** : ouvre la console Tailscale du device

## 🛠️ Développement

### Pre-commit hooks

```bash
pip install pre-commit
pre-commit install
```

### Linting

```bash
black src/ tests/
isort src/ tests/
flake8 src/ tests/
mypy src/ids
```

## 📝 License

MIT

## 🤝 Contribution

Les contributions sont les bienvenues ! Ouvre une issue ou une PR.

## 📧 Contact

- GitHub: [@alexisdeudon01](https://github.com/alexisdeudon01)
- Repo: https://github.com/alexisdeudon01/oi
