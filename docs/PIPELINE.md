# 🔄 Pipeline IDS - Architecture et Flux de Données

## Vue d'ensemble

Le pipeline IDS (Intrusion Detection System) est un système de détection d'intrusions passif qui analyse le trafic réseau en temps réel pour identifier les menaces de sécurité.

## Architecture Réseau

```
Internet
   │
   ▼
[Routeur] (Port 1)
   │
   ▼
[TP-Link TL-SG108E Switch]
   │                    │
   │                    │ (Port Mirroring: Port 1 → Port 5)
   │                    │
   ▼                    ▼
[LAN]            [Raspberry Pi] (Port 5/eth0)
                      │
                      ▼
              [Suricata IDS]
                      │
                      ▼
                  [Vector]
                      │
                      ▼
              [OpenSearch/Elasticsearch]
                      │
                      ▼
              [Dashboard de Monitoring]
```

### Composants Réseau

1. **Routeur** : Point d'entrée/sortie du trafic Internet
2. **TP-Link TL-SG108E** : Switch managé avec port mirroring
   - Port 1 : Connecté au routeur (trafic source)
   - Port 5 : Connecté au Raspberry Pi (destination du mirror)
   - Configuration : Port 1 → Port 5 (copie du trafic)
3. **Raspberry Pi** : Capteur IDS passif
   - Interface `eth0` en mode promiscuous
   - Reçoit une copie de TOUT le trafic réseau
   - N'interfère pas avec le trafic normal

## Flux de Données (Pipeline)

### Étape 1 : Capture du Trafic (Port Mirroring)

```
Trafic Internet → Routeur → Switch (Port 1)
                              │
                              ├─→ LAN (trafic normal)
                              └─→ Raspberry Pi (Port 5/eth0) [MIRROR]
```

**Caractéristiques :**
- **Passif** : Le Pi ne modifie pas le trafic
- **Promiscuous Mode** : `eth0` reçoit tous les paquets, même ceux non destinés au Pi
- **Transparent** : Aucun impact sur les performances réseau

**Configuration :**
```bash
# Activer le mode promiscuous
sudo ip link set eth0 promisc on

# Vérifier
ip link show eth0 | grep PROMISC
```

### Étape 2 : Inspection par Suricata

```
eth0 (trafic mirroiré)
   │
   ▼
[Suricata] - Analyse en temps réel
   │
   ├─→ Détection de signatures (règles ET-Open)
   ├─→ Analyse protocolaire (HTTP, DNS, TLS, etc.)
   ├─→ Détection d'anomalies
   └─→ Génération d'alertes
   │
   ▼
/var/log/suricata/eve.json (logs JSON structurés)
```

**Suricata** :
- **Moteur d'inspection** : Analyse les paquets réseau en temps réel
- **Règles de détection** : Utilise les règles ET-Open (Emerging Threats)
- **Format EVE JSON** : Logs structurés avec métadonnées complètes
- **Types d'événements** :
  - `alert` : Alertes de sécurité détectées
  - `http` : Requêtes HTTP analysées
  - `dns` : Requêtes DNS
  - `tls` : Connexions TLS/SSL
  - `flow` : Informations de flux réseau

**Exemple d'alerte EVE :**
```json
{
  "timestamp": "2024-02-04T12:34:56.789Z",
  "event_type": "alert",
  "src_ip": "192.168.1.100",
  "dest_ip": "10.0.0.1",
  "alert": {
    "action": "allowed",
    "gid": 1,
    "signature_id": 2012896,
    "signature": "ET MALWARE Known Malware IP",
    "category": "A Network Trojan was detected",
    "severity": 1
  }
}
```

**Configuration Suricata :**
```yaml
# /etc/suricata/suricata.yaml
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

### Étape 3 : Collecte et Enrichissement (Vector)

```
/var/log/suricata/eve.json
   │
   ▼
[Vector] - Agent de collecte et transformation
   │
   ├─→ Parsing JSON
   ├─→ Enrichissement (géolocalisation IP, etc.)
   ├─→ Filtrage et transformation
   ├─→ Agrégation
   └─→ Buffering
   │
   ▼
[OpenSearch/Elasticsearch] (via HTTP/HTTPS)
```

**Vector** :
- **Collecte** : Lit les logs Suricata en temps réel (tail)
- **Transformation** : Parse, enrichit, filtre les données
- **Routage** : Envoie vers OpenSearch avec retry automatique
- **Buffering** : Gère les pannes réseau temporaires

**Configuration Vector :**
```toml
# vector.toml
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
```

### Étape 4 : Stockage et Indexation (OpenSearch/Elasticsearch)

```
Vector → HTTP POST
   │
   ▼
[OpenSearch Cluster]
   │
   ├─→ Indexation par date (logstash-2024.02.04)
   ├─→ Mapping automatique des champs
   ├─→ Réplication (si cluster multi-nœuds)
   └─→ Rétention configurable
   │
   ▼
Données indexées et recherchables
```

**OpenSearch/Elasticsearch** :
- **Indexation** : Un index par jour (ex: `suricata-2024.02.04`)
- **Recherche** : Requêtes full-text et agrégations
- **Visualisation** : Compatible avec Kibana/OpenSearch Dashboards
- **Rétention** : Politique de rétention configurable (ex: 30 jours)

**Structure des données :**
```json
{
  "@timestamp": "2024-02-04T12:34:56.789Z",
  "event_type": "alert",
  "src_ip": "192.168.1.100",
  "dest_ip": "10.0.0.1",
  "alert": {
    "signature": "ET MALWARE Known Malware IP",
    "severity": 1,
    "category": "A Network Trojan was detected"
  },
  "geoip": {
    "src_location": {"country": "US", "city": "New York"},
    "dest_location": {"country": "FR", "city": "Paris"}
  }
}
```

### Étape 5 : Monitoring et Visualisation (Dashboard)

```
OpenSearch
   │
   ├─→ API REST (requêtes)
   └─→ WebSocket (streaming)
   │
   ▼
[Dashboard FastAPI]
   │
   ├─→ Suricata Log Monitor (tail eve.json)
   ├─→ Elasticsearch Health Monitor
   ├─→ Network Stats (psutil)
   ├─→ System Health (CPU, RAM, Temp)
   ├─→ Tailscale Nodes
   └─→ AI Healing (Anthropic Claude)
   │
   ▼
Frontend Web (React/HTML)
   │
   ├─→ Alertes en temps réel (WebSocket)
   ├─→ Graphiques de trafic
   ├─→ Statut du pipeline
   └─→ Métriques système
```

**Dashboard** :
- **WebSocket** : Streaming d'alertes en temps réel
- **REST API** : Requêtes pour historique et statistiques
- **Monitoring** : Santé de tous les composants
- **Hardware** : LED GPIO pour alertes critiques

## Flux Complet Détaillé

### 1. Capture (Interface Réseau)

```python
# eth0 en mode promiscuous
ip link set eth0 promisc on

# Suricata écoute sur eth0
suricata -c /etc/suricata/suricata.yaml -i eth0
```

### 2. Détection (Suricata)

```
Paquet réseau → Suricata Engine
   │
   ├─→ Décodage protocolaire (Ethernet, IP, TCP, UDP, etc.)
   ├─→ Inspection des règles (ET-Open signatures)
   ├─→ Détection d'anomalies
   └─→ Génération d'événements
   │
   ▼
Écriture dans /var/log/suricata/eve.json
```

### 3. Collecte (Vector)

```
Vector lit eve.json (tail -f)
   │
   ├─→ Parse JSON
   ├─→ Enrichissement (géolocalisation, etc.)
   ├─→ Transformation (normalisation)
   └─→ Buffering
   │
   ▼
Envoi vers OpenSearch (HTTP POST)
```

### 4. Stockage (OpenSearch)

```
Vector → OpenSearch API
   │
   ├─→ Indexation (par date)
   ├─→ Mapping automatique
   └─→ Réplication (si cluster)
   │
   ▼
Données disponibles pour recherche/analyse
```

### 5. Visualisation (Dashboard)

```
Dashboard FastAPI
   │
   ├─→ Suricata: tail eve.json → WebSocket
   ├─→ OpenSearch: API queries → REST
   ├─→ Network: psutil → REST
   └─→ System: psutil → REST
   │
   ▼
Frontend affiche données en temps réel
```

## Composants Techniques

### Suricata

**Rôle** : Moteur d'inspection de paquets réseau
**Input** : Trafic réseau (eth0 en promiscuous)
**Output** : Logs EVE JSON structurés
**Règles** : ET-Open (Emerging Threats Open Rules)

**Mise à jour des règles :**
```bash
sudo suricata-update
sudo systemctl restart suricata
```

### Vector

**Rôle** : Agent de collecte et transformation de logs
**Input** : Fichiers logs (eve.json)
**Output** : OpenSearch/Elasticsearch
**Fonctions** : Parsing, enrichissement, buffering, retry

**Commandes :**
```bash
# Démarrer Vector
vector --config vector/vector.toml

# Vérifier la configuration
vector validate --config vector/vector.toml
```

### OpenSearch/Elasticsearch

**Rôle** : Moteur de recherche et d'analyse
**Input** : Données JSON de Vector
**Output** : API REST pour requêtes
**Fonctions** : Indexation, recherche, agrégation, visualisation

**Création du domaine :**
```bash
python scripts/configure_infrastructure.py
# ou
python -m ids.deploy.opensearch_domain creer_domaine
```

### Dashboard FastAPI

**Rôle** : Interface de monitoring et contrôle
**Input** : 
- Suricata logs (tail)
- OpenSearch API
- System metrics (psutil)
- Tailscale API

**Output** : 
- REST API
- WebSocket streaming
- Frontend HTML

## Exemple de Pipeline Complet

### Scénario : Attaque DDoS détectée

1. **Capture** : Paquets UDP volumineux arrivent sur le routeur
2. **Mirroring** : Switch copie le trafic vers le Pi (eth0)
3. **Suricata** : Détecte le pattern DDoS dans les règles ET-Open
4. **Alerte** : Génère un événement `alert` avec sévérité 1
5. **Log** : Écrit dans `/var/log/suricata/eve.json`
6. **Vector** : Lit l'alerte, enrichit avec géolocalisation
7. **OpenSearch** : Indexe l'alerte dans `suricata-2024.02.04`
8. **Dashboard** : 
   - Reçoit l'alerte via WebSocket
   - Affiche dans l'interface
   - Fait clignoter la LED rouge (GPIO Pin 17)
   - Enregistre dans l'historique

### Timeline

```
T+0ms   : Paquet arrive sur routeur
T+1ms   : Switch copie vers Pi
T+2ms   : Suricata analyse le paquet
T+3ms   : Alerte générée (si détection)
T+4ms   : Écriture dans eve.json
T+5ms   : Vector lit et parse
T+10ms  : Vector envoie vers OpenSearch
T+50ms  : OpenSearch indexe
T+100ms : Dashboard affiche l'alerte
T+101ms : LED clignote (si sévérité 1)
```

## Monitoring du Pipeline

### Vérification des composants

```bash
# Suricata
sudo systemctl status suricata
sudo suricatasc -c "uptime"

# Vector
sudo systemctl status vector
vector validate --config vector/vector.toml

# OpenSearch
curl https://search-ids-domain-xxx.us-east-1.es.amazonaws.com/_cluster/health

# Dashboard
curl http://localhost:8080/api/pipeline/status
```

### Métriques clés

- **Latence** : Temps entre capture et affichage (< 1 seconde)
- **Throughput** : Paquets/seconde traités par Suricata
- **Alertes** : Nombre d'alertes par jour
- **Stockage** : Taille des indices OpenSearch
- **Disponibilité** : Uptime des composants

## Résolution de Problèmes

### Pipeline bloqué

1. **Vérifier Suricata** : `sudo systemctl status suricata`
2. **Vérifier Vector** : `sudo journalctl -u vector -f`
3. **Vérifier OpenSearch** : `curl https://endpoint/_cluster/health`
4. **Vérifier le dashboard** : `curl http://localhost:8080/api/health`

### Alertes manquantes

1. **Vérifier les règles** : `sudo suricata-update list-sources`
2. **Vérifier les logs** : `tail -f /var/log/suricata/eve.json`
3. **Vérifier Vector** : `vector top --config vector/vector.toml`

### Performance

1. **Suricata** : Ajuster `threads` dans `suricata.yaml`
2. **Vector** : Ajuster `batch_size` et `buffer`
3. **OpenSearch** : Augmenter `InstanceCount` si nécessaire

## Sécurité

- **Passif** : Le Pi ne modifie pas le trafic
- **Isolé** : Le Pi n'a pas d'accès direct au LAN
- **Chiffrement** : OpenSearch avec HTTPS/TLS
- **Authentification** : API keys pour Tailscale et OpenSearch
- **Logs** : Tous les événements sont tracés

## Évolutivité

- **Multi-capteurs** : Plusieurs Pi peuvent envoyer vers le même OpenSearch
- **Cluster** : OpenSearch peut être un cluster multi-nœuds
- **Rétention** : Politique de rétention configurable par index
- **Alerting** : Intégration possible avec Slack, PagerDuty, etc.
