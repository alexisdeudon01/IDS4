# 🔐 Configuration des Secrets

## Fichier secret.json

Tous les secrets doivent être stockés dans `secret.json` à la racine du projet.

## Structure minimale

```json
{
  "aws": {
    "access_key_id": "AKIA...",
    "secret_access_key": "..."
  },
  "tailscale": {
    "api_key": "tskey-api-..."
  }
}
```

**Note** : `elasticsearch`, `anthropic` et `dashboard` sont optionnels et non nécessaires pour le déploiement de base.

## Secrets Requis

### 🔴 Obligatoires

#### AWS (pour OpenSearch)
- **`aws.access_key_id`** : Clé d'accès AWS
  - Où l'obtenir : AWS Console → IAM → Users → Security credentials
  - Format : `AKIA...`
  
- **`aws.secret_access_key`** : Clé secrète AWS
  - Où l'obtenir : Même endroit que access_key_id
  - Format : Chaîne aléatoire longue

#### Tailscale (pour gestion du réseau)
- **`tailscale.api_key`** : Clé API Tailscale (OBLIGATOIRE)
  - Où l'obtenir : https://login.tailscale.com/admin/settings/keys
  - Format : `tskey-api-...`
  - Permissions : Nécessite les permissions pour créer des clés d'authentification
  
- **`tailscale.tailnet`** : Nom de votre tailnet (OPTIONNEL - auto-détecté)
  - Format : `votrenom.github` ou `votrenom.com`
  - **Le tailnet est détecté automatiquement depuis l'API key**
  - Vous pouvez laisser vide : `"tailnet": ""`

### 🟡 Optionnels (mais recommandés)

#### Elasticsearch/OpenSearch
- **`elasticsearch.username`** : Nom d'utilisateur OpenSearch
  - Par défaut : `admin` (si authentification activée)
  
- **`elasticsearch.password`** : Mot de passe OpenSearch
  - Nécessaire si OpenSearch a l'authentification activée

#### Anthropic (AI Healing) - OPTIONNEL - Non utilisé dans les scripts
- **`anthropic.api_key`** : Clé API Anthropic Claude (optionnel)
  - Où l'obtenir : https://console.anthropic.com/
  - Format : `sk-ant-...`
  - Utilisation : Diagnostic automatique des erreurs via endpoint `/api/ai-healing/diagnose`
  - **Note** : Non requis pour le déploiement, uniquement pour la fonctionnalité AI Healing dans le dashboard
  - **Non utilisé dans les scripts de déploiement** : Vous pouvez l'ignorer si vous ne voulez pas utiliser l'AI Healing

#### Tailscale OAuth (pour CI/CD uniquement)
- **`tailscale.oauth_client_id`** : OAuth Client ID
  - Où l'obtenir : https://login.tailscale.com/admin/oauth-clients
  - Format : `k...`
  
- **`tailscale.oauth_client_secret`** : OAuth Client Secret
  - Format : `tskey-client-...`

#### Anthropic (AI Healing) - OPTIONNEL - Non utilisé dans les scripts de déploiement
- **`anthropic.api_key`** : Clé API Anthropic Claude (optionnel)
  - Où l'obtenir : https://console.anthropic.com/
  - Format : `sk-ant-...`
  - Utilisation : Diagnostic automatique des erreurs via endpoint `/api/ai-healing/diagnose`
  - **Note** : Non requis pour le déploiement, uniquement pour la fonctionnalité AI Healing dans le dashboard

## Configuration

### 1. Créer secret.json

```bash
cp secret.json.example secret.json
nano secret.json
```

### 2. Remplir les secrets

**Minimum requis pour le dashboard :**
```json
{
  "aws": {
    "access_key_id": "VOTRE_ACCESS_KEY",
    "secret_access_key": "VOTRE_SECRET_KEY"
  },
  "tailscale": {
    "api_key": "tskey-api-..."
  }
}
```

**Note** : Le `tailnet` est détecté automatiquement depuis l'API key. Vous n'avez pas besoin de le spécifier !

**Configuration complète (avec options) :**
```json
{
  "aws": {
    "access_key_id": "AKIA...",
    "secret_access_key": "...",
    "session_token": ""
  },
  "tailscale": {
    "api_key": "tskey-api-...",
    "oauth_client_id": "k...",
    "oauth_client_secret": "tskey-client-..."
  },
  "elasticsearch": {
    "username": "admin",
    "password": "..."
  }
}
```

**Note** : Anthropic (AI Healing) est optionnel et n'est pas nécessaire pour le fonctionnement de base.

## Utilisation dans le code

Les secrets sont chargés automatiquement :

- **Dashboard** : Lit depuis les variables d'environnement (chargées depuis secret.json)
- **OpenSearch** : Utilise `aws.access_key_id` et `aws.secret_access_key`
- **Tailscale** : Utilise `tailscale.tailnet` et `tailscale.api_key`
- **Elasticsearch** : Utilise `elasticsearch.username` et `elasticsearch.password`
- **AI Healing** : Utilise `anthropic.api_key`

## Sécurité

⚠️ **IMPORTANT** :
- Ne jamais commiter `secret.json` dans Git
- Ajouter `secret.json` au `.gitignore`
- Utiliser `secret.json.example` comme template
- Changer les secrets régulièrement
- Utiliser des clés avec permissions minimales

## Variables d'environnement alternatives

Vous pouvez aussi utiliser des variables d'environnement au lieu de secret.json :

```bash
export AWS_ACCESS_KEY_ID="AKIA..."
export AWS_SECRET_ACCESS_KEY="..."
export TAILSCALE_TAILNET="yourname.github"
export TAILSCALE_API_KEY="tskey-api-..."
export ELASTICSEARCH_USERNAME="admin"
export ELASTICSEARCH_PASSWORD="..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

## Où obtenir les clés

### AWS
1. AWS Console → IAM
2. Users → Votre utilisateur
3. Security credentials → Create access key

### Tailscale
1. https://login.tailscale.com/admin/settings/keys
2. Créer une nouvelle clé API
3. Permissions : `devices:write`, `keys:write`

### Anthropic
1. https://console.anthropic.com/
2. API Keys → Create Key

### OpenSearch
- Généré lors de la création du domaine OpenSearch
- Ou configuré dans AWS Console → OpenSearch → Security
