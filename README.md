# Architecture du pipeline SOC IDS

Ce document décrit l’architecture cible du pipeline SOC pour un IDS Suricata déployé sur **Raspberry Pi 5 (8 GB RAM)**, avec ingestion vers **AWS OpenSearch**, orchestration Python, parallélisme contrôlé et déploiement Docker.

---

## 0) Contexte matériel & contraintes

### Raspberry Pi cible

| Élément          | Valeur                       |
| ---------------- | ---------------------------- |
| Modèle           | Raspberry Pi 5               |
| RAM              | 8 GB                         |
| CPU              | 4 × Cortex-A76               |
| OS               | Debian GNU/Linux 13 (Trixie) |
| IP fixe          | **192.168.178.66**           |
| Interface réseau | **eth0 uniquement**          |
| Swap             | 2 GB                         |
| Stockage         | microSD 119 GB               |

### Contraintes clés

* **CPU total utilisé ≤ 70 %**
* **RAM totale utilisée ≤ 70 %**
* Tolérance aux pics de trafic (burst IDS)
* Aucun blocage réseau ou CPU lors des tests AWS
* Pipeline résilient (buffer + backpressure)

---

## 1) Bibliothèques nécessaires

### Python (`requirements.txt`)

| Bibliothèque      | Rôle                                    |
| ----------------- | --------------------------------------- |
| boto3             | SDK AWS (création / gestion OpenSearch) |
| opensearch-py     | Client OpenSearch (bulk, health checks) |
| uvloop            | Boucle asyncio ultra-performante        |
| asyncio           | Parallélisme I/O                        |
| orjson            | Sérialisation JSON rapide               |
| msgpack-python    | Format binaire rapide (interne)         |
| aioredis          | Buffer Redis asynchrone                 |
| PyYAML            | Parsing `config.yaml`                   |
| watchdog          | Suivi temps réel de `eve.json`          |
| requests          | HTTP simple                             |
| prometheus-client | Export métriques                        |
| GitPython         | Commit / push sur branche `dev`         |
| pytest            | Tests                                   |

---

## 2) Stratégie globale

Le projet repose sur une **stratégie “pipeline orienté flux”**, découplée, asynchrone et résiliente.

### Principes clés

* **Découplage** : Suricata ≠ Vector ≠ OpenSearch
* **Backpressure** : Redis absorbe les pics
* **Async first** : aucun appel réseau bloquant
* **Configuration unique** : `config.yaml`
* **Automatisation totale** : zéro configuration manuelle
* **Observabilité native** : métriques partout

---

## 3) Qu’est-ce que l’AWS SDK (boto3) ?

`boto3` est le **SDK officiel AWS pour Python**.

Il permet :

* Authentification via **SigV4**
* Appels API sécurisés
* Création / description de ressources AWS
* Polling d’état non bloquant

### Utilisation dans ce projet

* Création ou récupération du **OpenSearch Domain**
* Attente de l’état `ACTIVE`
* Récupération de l’endpoint
* Application d’index templates
* Tests de connectivité

---

## 4) Qu’est-ce que le pipeline SOC ?

Un pipeline SOC est une **chaîne continue de traitement de logs sécurité**.

### Chaîne logique

1. Capture réseau (Suricata)
2. Écriture JSON (`eve.json`)
3. Parsing / mapping ECS (Vector)
4. Bufferisation (Redis)
5. Ingestion bulk (OpenSearch)
6. Visualisation / alertes
7. Monitoring système & pipeline

### Schéma simplifié

```
Suricata → Vector → Redis → OpenSearch
              ↓
         Prometheus → Grafana
```

---

## 5) Structures de données

### 5.1 Suricata JSON (eve.json)

```json
{
  "timestamp": "2026-02-01T02:10:00.123Z",
  "event_type": "alert",
  "src_ip": "192.168.178.5",
  "dest_ip": "10.0.0.10",
  "alert": {
    "signature": "ET SCAN ...",
    "severity": 2
  }
}
```

---

### 5.2 ECS (après Vector)

```json
{
  "@timestamp": "2026-02-01T02:10:00.123Z",
  "event": {
    "kind": "alert",
    "category": "network"
  },
  "source": {
    "ip": "192.168.178.5"
  },
  "destination": {
    "ip": "10.0.0.10"
  },
  "suricata": {
    "signature": "ET SCAN ...",
    "severity": 2
  }
}
```

---

### 5.3 Bulk OpenSearch (NDJSON)

```
{ "index": { "_index": "suricata-2026.02.01" } }
{ "doc ECS" }
```

---

## 6) Phases du système

### Phase A — Initialisation Raspberry Pi

* Désactiver toutes les interfaces sauf `eth0`
* Configurer firewall minimal
* Créer RAM disk pour logs
* Installer Docker & Python

---

### Phase B — Provisioning AWS

* Charger `config.yaml`
* Vérifier credentials
* Créer ou détecter domaine
* Attendre `ACTIVE`
* Sauvegarder endpoint

---

### Phase C — Tests réseau (asynchrones)

Exécutés **en parallèle** :

* DNS
* TLS
* Bulk

---

### Phase D — Génération de configurations

* `suricata.yaml`
* `vector.toml`
* `docker-compose.yml`
* `prometheus.yml`
* Dashboards Grafana

---

### Phase E — Déploiement Docker

* Redis
* Vector
* Prometheus
* Grafana

---

### Phase F — Ingestion & monitoring

* Tail `eve.json`
* Vector → Redis → OpenSearch
* Export métriques
* Alerting

---

### Phase G — Git (branche dev)

* Vérification branche `dev`
* Commit automatique
* Push sur `dev`

---

## 7) Conteneurs Docker

| Conteneur  | Rôle                |
| ---------- | ------------------- |
| Redis      | Buffer backpressure |
| Vector     | Parsing + ingestion |
| Prometheus | Collecte métriques  |
| Grafana    | Dashboards          |

---

## 8) Parallélisme & multithreading

### 8.1 Parallélisme Python (I/O)

Utilisé pour :

* DNS
* TLS
* Tests bulk
* Monitoring

```python
await asyncio.gather(
  test_dns(),
  test_tls(),
  test_bulk()
)
```

### 8.2 Vector (natif)

Vector est écrit en **Rust**, multi-thread nativement :

* Lecture fichiers
* Parsing ECS
* Batching
* Retry/backoff

---

## 9) Gestion CPU & RAM (< 70 %)

### Répartition CPU

| Composant  | CPU     |
| ---------- | ------- |
| Suricata   | 3 cœurs |
| Vector     | 1 cœur  |
| Redis      | faible  |
| Prometheus | faible  |
| Grafana    | faible  |

### Répartition RAM

| Composant    | RAM max |
| ------------ | ------- |
| Suricata     | ~4 GB   |
| Vector       | ~1 GB   |
| Redis        | ~512 MB |
| Docker stack | ~1 GB   |
| Libre        | >1 GB   |

### Mécanismes de contrôle

* Limites Docker (`mem_limit`, `cpus`)
* Batching Vector
* Chunking async Python
* Garbage collection Python forcée
* Rotation logs RAM disk

---

## 10) Réseau & sécurité

### Interface

* **eth0 uniquement**
* IP : **192.168.178.66**

```bash
ip link set wlan0 down
ip link set usb0 down
```

### Firewall minimal

```bash
iptables -A OUTPUT -o eth0 -p tcp --dport 443 -j ACCEPT
iptables -A OUTPUT -o eth0 -p udp --dport 53 -j ACCEPT
iptables -P OUTPUT DROP
iptables -P INPUT DROP
```

---

## 11) Agent SOC

Le projet inclut un **agent SOC Python** qui :

* Orchestre toutes les phases
* Surveille l’état du pipeline
* Expose métriques Prometheus
* Gère les retries
* Contrôle l’utilisation CPU/RAM
* Peut être lancé comme **service systemd**

👉 L’agent est le **cerveau du système**.

---

## 12) Amazon Q dans VS Code

### Prérequis

* Extension **AWS Toolkit / Amazon Q** installée
* Profil AWS déjà configuré : **`moi33`**
* Variables AWS déjà présentes

### Configuration

Dans VS Code :

1. Ouvrir **AWS Toolkit**
2. Sélectionner le profil **`moi33`**
3. Vérifier la région (`eu-central-1`)

### Utilisation avec ce projet

Amazon Q peut :

* Expliquer le code
* Générer des tests
* Vérifier la config AWS
* Aider à déboguer Vector / Suricata

Aucune configuration supplémentaire requise.

---

## 13) Résumé final

✔ Architecture robuste
✔ Async & multithread contrôlé
✔ Limites CPU/RAM respectées
✔ Observabilité complète
✔ Sécurité réseau stricte
✔ Déploiement reproductible
✔ Agent SOC central
✔ Compatible Amazon Q / VS Code
