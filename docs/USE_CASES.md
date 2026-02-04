# 📋 Use Cases Dashboard IDS - Vue Utilisateur (Complet)

## 🎯 Introduction

Le Dashboard IDS est une **application web unique** qui centralise toute la gestion, la configuration et le monitoring du système IDS basé sur Raspberry Pi. 

### Architecture Globale

**Dashboard Unique** : Tous les paramètres, configurations et secrets sont stockés dans une **base de données relationnelle** (SQLite en développement, PostgreSQL en production) gérée par le backend FastAPI. Le frontend React ne fait que l'affichage et l'interaction utilisateur, toutes les opérations passent par des API REST.

**Déploiement** : Un **script Python unique** (`deploy.py`) à la racine du projet permet de déployer l'ensemble du dashboard sur le Raspberry Pi. Ce script demande les informations minimales (IP Pi, user SSH, password SSH, password sudo) et écrit tout dans `secret.json` localement. Il upload ensuite tout le code sur le Pi, configure le service systemd, et démarre le dashboard.

**Service Systemd** : Le dashboard tourne comme un service systemd (`ids-dashboard.service`) qui démarre automatiquement au boot et redémarre en cas d'erreur.

**Déploiement Automatique au Premier Accès** : Lorsque l'utilisateur ouvre le dashboard pour la première fois, une **étape de déploiement automatique** s'exécute en live :
- Vérification de la connectivité Tailscale
- Création/configuration du domaine OpenSearch
- Configuration de Suricata, Vector, Elasticsearch
- Démarrage des services systemd
- Vérification de chaque étape avec try/catch partout
- En cas d'erreur, le système tente de déterminer automatiquement la cause et affiche un diagnostic détaillé

**Base de Données Centralisée** : Tous les paramètres de configuration (AWS, Tailscale, Suricata, Vector, Elasticsearch, Docker, etc.) sont stockés dans la base de données. Plus de fichiers YAML/TOML/JSON de configuration - tout est géré via le dashboard et la DB.

---

## Use Cases Utilisateur

### 1. Monitoring en Temps Réel

**En tant qu'utilisateur, je veux voir les alertes de sécurité en temps réel** pour être immédiatement informé des menaces détectées sur mon réseau.

**En tant qu'utilisateur, je veux voir le statut de chaque composant du pipeline** (Suricata, Vector, Elasticsearch) pour savoir si tout fonctionne correctement.

**En tant qu'utilisateur, je veux voir les métriques de santé du Raspberry Pi** (CPU, RAM, Disque, Température) pour m'assurer que le système ne surchauffe pas et a suffisamment de ressources.

**En tant qu'utilisateur, je veux voir le trafic réseau en temps réel** sur l'interface mirroirée pour vérifier que le port mirroring fonctionne et que le trafic est bien capturé.

**En tant qu'utilisateur, je veux voir l'état du cluster Elasticsearch** pour m'assurer que les données sont bien stockées et accessibles.

### 2. Configuration de l'Infrastructure

**En tant qu'utilisateur, je veux configurer automatiquement le réseau Tailscale** sans avoir à connaître les détails techniques, juste en fournissant ma clé API.

**En tant qu'utilisateur, je veux créer automatiquement le domaine OpenSearch** depuis le dashboard sans avoir à utiliser l'interface AWS, en un seul clic.

**En tant qu'utilisateur, je veux vérifier que mon infrastructure est correctement configurée** pour m'assurer que tout est prêt avant de démarrer la surveillance.

### 3. Diagnostic et Résolution de Problèmes

**En tant qu'utilisateur, je veux voir les problèmes détectés au démarrage** pour corriger les erreurs de configuration avant qu'elles n'affectent le système.

**En tant qu'utilisateur, je veux vérifier que le port mirroring est actif** pour m'assurer que le switch copie bien le trafic vers le Raspberry Pi.

**En tant qu'utilisateur, je veux voir un diagnostic automatique des erreurs** avec des suggestions de résolution pour corriger rapidement les problèmes.

### 4. Visualisation et Analyse

**En tant qu'utilisateur, je veux voir un historique des alertes récentes** pour comprendre les tendances et les patterns d'attaque.

**En tant qu'utilisateur, je veux voir les statistiques de trafic réseau** (débit, paquets) pour comprendre le volume de données analysées.

**En tant qu'utilisateur, je veux visualiser mon réseau Tailscale sous forme de graphe interactif** avec tous les nœuds connectés, leur latence, et pouvoir cliquer sur un nœud pour accéder à sa console Tailscale.

**En tant qu'utilisateur, je veux voir la liste de tous les services systemd** (Suricata, Vector, Dashboard, etc.) avec leur statut pour savoir quels services tournent ou sont arrêtés.

**En tant qu'utilisateur, je veux voir la liste des index Elasticsearch** créés quotidiennement pour comprendre combien de données sont stockées chaque jour.

### 5. Gestion du Réseau Tailscale

**En tant qu'utilisateur, je veux ajouter un nouveau nœud au réseau Tailscale** depuis le dashboard en fournissant juste le nom du nœud et l'adresse IP, sans avoir à générer manuellement des clés d'authentification.

**En tant qu'utilisateur, je veux créer des clés d'authentification Tailscale** réutilisables ou éphémères depuis le dashboard pour enregistrer de nouveaux appareils.

**En tant qu'utilisateur, je veux voir tous les nœuds Tailscale connectés** avec leur statut (online/offline), leur dernière connexion, et leurs tags.

### 6. Gestion Elasticsearch/OpenSearch

**En tant qu'utilisateur, je veux voir la liste des index Elasticsearch** avec leur taille, leur date de création, et le nombre de documents pour gérer l'espace de stockage.

**En tant qu'utilisateur, je veux créer des index patterns** pour organiser mes données de logs selon mes besoins.

**En tant qu'utilisateur, je veux voir les statistiques des index** (taille, nombre de documents, date de création) pour planifier la rétention des données.

**En tant qu'utilisateur, je veux créer des dashboards Elasticsearch/OpenSearch Dashboards** depuis le dashboard IDS pour visualiser mes données de logs.

### 7. Alertes et Notifications

**En tant qu'utilisateur, je veux être alerté visuellement quand une menace critique est détectée** (LED qui clignote) pour réagir immédiatement même si je ne regarde pas l'écran.

**En tant qu'utilisateur, je veux voir les alertes classées par sévérité** pour prioriser mon attention sur les menaces les plus graves.

### 8. Accès et Disponibilité

**En tant qu'utilisateur, je veux accéder au dashboard depuis n'importe quel appareil sur mon réseau** pour monitorer mon IDS même quand je ne suis pas devant le Raspberry Pi.

**En tant qu'utilisateur, je veux que le dashboard soit toujours accessible** même si un composant plante, pour pouvoir diagnostiquer et redémarrer les services.

### 9. Performance et Multithreading

**En tant qu'utilisateur, je veux que le dashboard traite plusieurs opérations en parallèle** (lecture des logs, requêtes API, calculs de métriques) pour que l'interface reste réactive même quand beaucoup de données arrivent.

**En tant qu'utilisateur, je veux que les mises à jour des différentes sections se fassent simultanément** sans que l'une bloque l'autre, pour avoir une vue complète et à jour en permanence.

### 10. Déploiement Initial

**En tant qu'utilisateur, je veux déployer le dashboard en une seule commande** en fournissant juste l'IP du Pi, le user SSH, le password SSH et le password sudo.

**En tant qu'utilisateur, je veux que le déploiement initial configure automatiquement tous les services** (Suricata, Vector, Elasticsearch, Tailscale, OpenSearch) sans intervention manuelle.

---

## 📊 Architecture Base de Données

### Schéma Complet

Tous les paramètres suivants sont stockés dans la base de données :

#### Table `secrets`
- `id` (INTEGER PRIMARY KEY)
- `aws_access_key_id` (TEXT, ENCRYPTED)
- `aws_secret_access_key` (TEXT, ENCRYPTED)
- `aws_session_token` (TEXT, ENCRYPTED, NULLABLE)
- `tailscale_api_key` (TEXT, ENCRYPTED)
- `tailscale_oauth_client_id` (TEXT, ENCRYPTED, NULLABLE)
- `tailscale_oauth_client_secret` (TEXT, ENCRYPTED, NULLABLE)
- `elasticsearch_username` (TEXT, NULLABLE)
- `elasticsearch_password` (TEXT, ENCRYPTED, NULLABLE)
- `pi_ssh_user` (TEXT)
- `pi_ssh_password` (TEXT, ENCRYPTED)
- `pi_sudo_password` (TEXT, ENCRYPTED)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

#### Table `aws_config`
- `id` (INTEGER PRIMARY KEY)
- `region` (TEXT, DEFAULT: "eu-central-1")
- `domain_name` (TEXT, DEFAULT: "suricata-prod")
- `opensearch_endpoint` (TEXT, NULLABLE)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

#### Table `raspberry_pi_config`
- `id` (INTEGER PRIMARY KEY)
- `pi_ip` (TEXT)
- `home_net` (TEXT, DEFAULT: "192.168.178.0/24")
- `network_interface` (TEXT, DEFAULT: "eth0")
- `cpu_limit_percent` (REAL, DEFAULT: 70.0)
- `ram_limit_percent` (REAL, DEFAULT: 70.0)
- `swap_size_gb` (INTEGER, DEFAULT: 2)
- `cpu_limit_medium_percent` (REAL, DEFAULT: 75.0)
- `ram_limit_medium_percent` (REAL, DEFAULT: 75.0)
- `cpu_limit_high_percent` (REAL, DEFAULT: 80.0)
- `ram_limit_high_percent` (REAL, DEFAULT: 80.0)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

#### Table `suricata_config`
- `id` (INTEGER PRIMARY KEY)
- `log_path` (TEXT, DEFAULT: "/mnt/ram_logs/eve.json")
- `config_path` (TEXT, DEFAULT: "suricata/suricata.yaml")
- `rules_path` (TEXT, DEFAULT: "suricata/rules")
- `eve_log_payload` (BOOLEAN, DEFAULT: false)
- `eve_log_packet` (BOOLEAN, DEFAULT: false)
- `eve_log_http` (BOOLEAN, DEFAULT: true)
- `eve_log_dns` (BOOLEAN, DEFAULT: true)
- `eve_log_tls` (BOOLEAN, DEFAULT: true)
- `eve_log_flow` (BOOLEAN, DEFAULT: true)
- `eve_log_stats` (BOOLEAN, DEFAULT: true)
- `default_log_dir` (TEXT, DEFAULT: "/mnt/ram_logs")
- `home_net` (TEXT, DEFAULT: "any")
- `external_net` (TEXT, DEFAULT: "any")
- `http_ports` (TEXT, DEFAULT: "80")
- `ssh_ports` (TEXT, DEFAULT: "22")
- `smtp_ports` (TEXT, DEFAULT: "25")
- `dns_ports` (TEXT, DEFAULT: "53")
- `tls_ports` (TEXT, DEFAULT: "443")
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

#### Table `vector_config`
- `id` (INTEGER PRIMARY KEY)
- `index_pattern` (TEXT, DEFAULT: "suricata-ids2-%Y.%m.%d")
- `log_read_path` (TEXT, DEFAULT: "/mnt/ram_logs/eve.json")
- `disk_buffer_max_size` (TEXT, DEFAULT: "100 GiB")
- `redis_buffer_max_size` (TEXT, DEFAULT: "10 GiB")
- `opensearch_buffer_max_size` (TEXT, DEFAULT: "50 GiB")
- `batch_max_events` (INTEGER, DEFAULT: 500)
- `batch_timeout_secs` (INTEGER, DEFAULT: 2)
- `read_from` (TEXT, DEFAULT: "beginning")
- `fingerprint_bytes` (INTEGER, DEFAULT: 1024)
- `redis_host` (TEXT, DEFAULT: "redis")
- `redis_port` (INTEGER, DEFAULT: 6379)
- `redis_key` (TEXT, DEFAULT: "vector_logs")
- `opensearch_compression` (TEXT, DEFAULT: "gzip")
- `opensearch_request_timeout_secs` (INTEGER, DEFAULT: 30)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

#### Table `redis_config`
- `id` (INTEGER PRIMARY KEY)
- `host` (TEXT, DEFAULT: "redis")
- `port` (INTEGER, DEFAULT: 6379)
- `db` (INTEGER, DEFAULT: 0)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

#### Table `prometheus_config`
- `id` (INTEGER PRIMARY KEY)
- `port` (INTEGER, DEFAULT: 9100)
- `docker_port` (INTEGER, DEFAULT: 9090)
- `update_interval` (INTEGER, DEFAULT: 5)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

#### Table `grafana_config`
- `id` (INTEGER PRIMARY KEY)
- `docker_port` (INTEGER, DEFAULT: 3000)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

#### Table `docker_config`
- `id` (INTEGER PRIMARY KEY)
- `compose_file` (TEXT, DEFAULT: "docker/docker-compose.yml")
- `vector_cpu` (REAL, DEFAULT: 1.0)
- `vector_ram_mb` (INTEGER, DEFAULT: 1024)
- `redis_cpu` (REAL, DEFAULT: 0.5)
- `redis_ram_mb` (INTEGER, DEFAULT: 512)
- `prometheus_cpu` (REAL, DEFAULT: 0.2)
- `prometheus_ram_mb` (INTEGER, DEFAULT: 256)
- `grafana_cpu` (REAL, DEFAULT: 0.2)
- `grafana_ram_mb` (INTEGER, DEFAULT: 256)
- `cadvisor_cpu` (REAL, DEFAULT: 0.1)
- `cadvisor_ram_mb` (INTEGER, DEFAULT: 64)
- `node_exporter_cpu` (REAL, DEFAULT: 0.1)
- `node_exporter_ram_mb` (INTEGER, DEFAULT: 64)
- `fastapi_cpu` (REAL, DEFAULT: 0.5)
- `fastapi_ram_mb` (INTEGER, DEFAULT: 256)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

#### Table `tailscale_config`
- `id` (INTEGER PRIMARY KEY)
- `tailnet` (TEXT, NULLABLE, AUTO-DETECTED)
- `dns_enabled` (BOOLEAN, DEFAULT: true)
- `magic_dns` (BOOLEAN, DEFAULT: true)
- `exit_node_enabled` (BOOLEAN, DEFAULT: false)
- `subnet_routes` (TEXT, JSON ARRAY, DEFAULT: "[]")
- `deployment_mode` (TEXT, DEFAULT: "auto")
- `default_tags` (TEXT, JSON ARRAY, DEFAULT: '["ci", "ids2"]')
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

#### Table `fastapi_config`
- `id` (INTEGER PRIMARY KEY)
- `port` (INTEGER, DEFAULT: 8080)
- `host` (TEXT, DEFAULT: "0.0.0.0")
- `log_level` (TEXT, DEFAULT: "INFO")
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

#### Table `resource_controller_config`
- `id` (INTEGER PRIMARY KEY)
- `check_interval` (INTEGER, DEFAULT: 1)
- `throttling_enabled` (BOOLEAN, DEFAULT: true)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

#### Table `connectivity_config`
- `id` (INTEGER PRIMARY KEY)
- `check_interval` (INTEGER, DEFAULT: 10)
- `max_retries` (INTEGER, DEFAULT: 5)
- `initial_backoff` (REAL, DEFAULT: 1.0)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

#### Table `services_status`
- `id` (INTEGER PRIMARY KEY)
- `service_name` (TEXT, UNIQUE)
- `status` (TEXT, CHECK: "active", "inactive", "failed", "unknown")
- `enabled` (BOOLEAN)
- `last_check` (TIMESTAMP)
- `last_error` (TEXT, NULLABLE)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

#### Table `deployment_history`
- `id` (INTEGER PRIMARY KEY)
- `deployment_type` (TEXT, CHECK: "initial", "update", "rollback")
- `component` (TEXT, CHECK: "dashboard", "suricata", "vector", "elasticsearch", "tailscale", "opensearch", "all")
- `status` (TEXT, CHECK: "success", "failed", "in_progress")
- `error_message` (TEXT, NULLABLE)
- `error_diagnosis` (TEXT, NULLABLE)
- `started_at` (TIMESTAMP)
- `completed_at` (TIMESTAMP, NULLABLE)
- `created_at` (TIMESTAMP)

#### Table `error_logs`
- `id` (INTEGER PRIMARY KEY)
- `component` (TEXT)
- `error_type` (TEXT)
- `error_message` (TEXT)
- `traceback` (TEXT, NULLABLE)
- `diagnosis` (TEXT, NULLABLE)
- `resolved` (BOOLEAN, DEFAULT: false)
- `resolved_at` (TIMESTAMP, NULLABLE)
- `created_at` (TIMESTAMP)

#### Table `system_metrics`
- `id` (INTEGER PRIMARY KEY)
- `cpu_percent` (REAL)
- `ram_percent` (REAL)
- `disk_percent` (REAL)
- `temperature` (REAL, NULLABLE)
- `network_rx_bytes` (INTEGER)
- `network_tx_bytes` (INTEGER)
- `network_rx_packets` (INTEGER)
- `network_tx_packets` (INTEGER)
- `recorded_at` (TIMESTAMP)

#### Table `alerts`
- `id` (INTEGER PRIMARY KEY)
- `signature_id` (INTEGER)
- `signature` (TEXT)
- `severity` (INTEGER)
- `src_ip` (TEXT)
- `dest_ip` (TEXT)
- `src_port` (INTEGER, NULLABLE)
- `dest_port` (INTEGER, NULLABLE)
- `protocol` (TEXT, NULLABLE)
- `timestamp` (TIMESTAMP)
- `payload` (TEXT, NULLABLE)
- `created_at` (TIMESTAMP)

#### Table `tailscale_nodes`
- `id` (INTEGER PRIMARY KEY)
- `node_id` (TEXT, UNIQUE)
- `hostname` (TEXT)
- `ip` (TEXT)
- `status` (TEXT, CHECK: "online", "offline")
- `last_seen` (TIMESTAMP, NULLABLE)
- `tags` (TEXT, JSON ARRAY)
- `latency_ms` (REAL, NULLABLE)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

#### Table `elasticsearch_indices`
- `id` (INTEGER PRIMARY KEY)
- `index_name` (TEXT, UNIQUE)
- `size_bytes` (INTEGER)
- `document_count` (INTEGER)
- `creation_date` (TIMESTAMP)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

#### Table `elasticsearch_index_patterns`
- `id` (INTEGER PRIMARY KEY)
- `pattern_name` (TEXT, UNIQUE)
- `pattern` (TEXT)
- `time_field` (TEXT, DEFAULT: "@timestamp")
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

#### Table `elasticsearch_dashboards`
- `id` (INTEGER PRIMARY KEY)
- `dashboard_name` (TEXT, UNIQUE)
- `dashboard_id` (TEXT, UNIQUE)
- `description` (TEXT, NULLABLE)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

---

## 🚀 Script de Déploiement (`deploy.py`)

### Description

Script Python unique à la racine du projet qui :
1. Demande à l'utilisateur : IP Pi, user SSH, password SSH, password sudo
2. Écrit ces informations dans `secret.json` (local, jamais commité)
3. Upload tout le code sur le Pi via SSH/SCP
4. Configure le service systemd
5. Démarre le dashboard
6. Vérifie que tout fonctionne

### Interface Utilisateur

```python
# Exemple d'exécution
$ python deploy.py

=== Déploiement Dashboard IDS ===

IP du Raspberry Pi: 192.168.1.100
Utilisateur SSH (défaut: pi): pi
Mot de passe SSH: ********
Mot de passe sudo: ********

Vérification de la connectivité...
✅ Connexion SSH réussie

Upload du code...
✅ Code uploadé

Configuration du service systemd...
✅ Service configuré

Démarrage du dashboard...
✅ Dashboard démarré

Vérification...
✅ Dashboard accessible sur http://192.168.1.100:8080

=== Déploiement terminé avec succès ===
```

### Fonctionnalités

- Vérification des dépendances locales (Python, SSH, rsync)
- Test de connectivité SSH
- Upload du code (frontend + backend)
- Installation des dépendances Python sur le Pi
- Configuration du service systemd
- Démarrage automatique
- Vérification de santé

---

## 📝 Inputs Utilisateur Requis

### Inputs pour le Script de Déploiement (`deploy.py`)

1. **IP du Raspberry Pi** : Adresse IP du Pi sur le réseau local ou Tailscale
2. **Utilisateur SSH** : Nom d'utilisateur SSH (défaut: `pi`)
3. **Mot de passe SSH** : Mot de passe pour la connexion SSH
4. **Mot de passe sudo** : Mot de passe pour les commandes sudo sur le Pi

Ces informations sont écrites dans `secret.json` (local, jamais commité dans Git).

### Inputs pour le Dashboard (Premier Accès)

Lors du premier accès au dashboard, l'utilisateur doit fournir :

1. **AWS Access Key ID** : Clé d'accès AWS pour créer/gérer OpenSearch
2. **AWS Secret Access Key** : Clé secrète AWS
3. **Tailscale API Key** : Clé API Tailscale (le tailnet est auto-détecté)

### Inputs Optionnels (via Dashboard)

4. **Elasticsearch Username** : Si authentification activée
5. **Elasticsearch Password** : Si authentification activée
6. **Tailscale OAuth Client ID** : Pour authentification OAuth (optionnel)
7. **Tailscale OAuth Client Secret** : Pour authentification OAuth (optionnel)

### Inputs pour Actions Spécifiques (via Dashboard)

8. **Pour ajouter un nœud Tailscale** :
   - Nom du nœud (hostname)
   - Adresse IP du nœud (optionnel, pour déploiement distant)
   - Tags (optionnel)
   - Type de nœud (device, subnet router, etc.)

9. **Pour créer un domaine OpenSearch** :
   - Nom du domaine (optionnel, utilise valeur par défaut si non fourni)
   - Région AWS (optionnel, utilise valeur par défaut)

10. **Pour créer une clé d'authentification Tailscale** :
    - Réutilisable (oui/non)
    - Éphémère (oui/non)
    - Tags (optionnel)

11. **Pour créer un index pattern Elasticsearch** :
    - Nom du pattern
    - Pattern (ex: "suricata-ids2-*")
    - Champ temporel (défaut: "@timestamp")

12. **Pour créer un dashboard Elasticsearch** :
    - Nom du dashboard
    - Description (optionnel)

---

## 🎯 Objectifs SMART

### 1. Monitoring en Temps Réel

#### Objectif 1.1 : Alertes en Temps Réel
- **Spécifique** : Afficher toutes les alertes Suricata détectées avec une latence inférieure à 1 seconde
- **Mesurable** : 100% des alertes affichées dans les 1 seconde suivant leur détection, 0% de perte d'alertes
- **Atteignable** : Utilisation de WebSocket pour streaming temps réel, tailing asynchrone des logs
- **Réaliste** : Architecture asynchrone Python + WebSocket permet cette latence
- **Temporel** : Fonctionnel dès le déploiement initial

#### Objectif 1.2 : Statut du Pipeline
- **Spécifique** : Afficher le statut (running/stopped/error) de chaque composant (Suricata, Vector, Elasticsearch)
- **Mesurable** : Mise à jour toutes les 5 secondes, 100% de précision du statut
- **Atteignable** : Vérification via systemctl et API Elasticsearch, stockage dans DB
- **Réaliste** : Polling toutes les 5 secondes ne surcharge pas le système
- **Temporel** : Disponible immédiatement après déploiement

#### Objectif 1.3 : Métriques Système
- **Spécifique** : Afficher CPU, RAM, Disque, Température du Raspberry Pi
- **Mesurable** : Mise à jour toutes les 5 secondes, précision à 1% près, stockage dans DB toutes les 30 secondes
- **Atteignable** : Utilisation de psutil pour les métriques système
- **Réaliste** : psutil est léger et ne consomme pas beaucoup de ressources
- **Temporel** : Fonctionnel dès le démarrage du dashboard

#### Objectif 1.4 : Trafic Réseau
- **Spécifique** : Afficher le débit (Rx/Tx) et le nombre de paquets sur l'interface eth0
- **Mesurable** : Mise à jour toutes les 5 secondes, calcul du débit en Gbps/Mbps/Kbps
- **Atteignable** : Utilisation de psutil.net_io_counters() pour les statistiques
- **Réaliste** : Calcul basé sur la différence entre deux mesures
- **Temporel** : Disponible dès que l'interface est configurée

#### Objectif 1.5 : Santé Elasticsearch
- **Spécifique** : Afficher le statut du cluster (green/yellow/red), nombre de nœuds, indices quotidiens
- **Mesurable** : Mise à jour toutes les 5 secondes, statut 100% fiable
- **Atteignable** : Requête API Elasticsearch pour /_cluster/health
- **Réaliste** : API Elasticsearch répond rapidement
- **Temporel** : Disponible dès la connexion à Elasticsearch configurée

### 2. Configuration de l'Infrastructure

#### Objectif 2.1 : Configuration Tailscale Automatique
- **Spécifique** : Détecter automatiquement le tailnet depuis l'API key et créer des clés d'authentification
- **Mesurable** : 100% de détection automatique du tailnet si API key valide, création de clé en < 5 secondes
- **Atteignable** : Appel API Tailscale /api/v2/user/self pour détecter le tailnet, stockage dans DB
- **Réaliste** : API Tailscale supporte cette fonctionnalité
- **Temporel** : Fonctionnel dès la première configuration

#### Objectif 2.2 : Création OpenSearch Automatique
- **Spécifique** : Créer un domaine OpenSearch depuis le dashboard en un seul clic
- **Mesurable** : Création réussie dans 100% des cas si credentials AWS valides, délai de 15-30 minutes
- **Atteignable** : Utilisation de boto3 pour créer le domaine via AWS API, configuration stockée en DB
- **Réaliste** : AWS OpenSearch API permet la création programmatique
- **Temporel** : Disponible via endpoint /api/setup/opensearch/create

#### Objectif 2.3 : Vérification Infrastructure
- **Spécifique** : Vérifier que Tailscale et OpenSearch sont correctement configurés
- **Mesurable** : Vérification en < 10 secondes, 100% de précision
- **Atteignable** : Tests de connectivité API pour chaque service
- **Réaliste** : Les APIs répondent rapidement
- **Temporel** : Disponible via endpoints /api/setup/tailnet/verify et /api/setup/opensearch/verify

### 3. Diagnostic et Résolution de Problèmes

#### Objectif 3.1 : Détection Problèmes au Démarrage
- **Spécifique** : Capturer et afficher les erreurs détectées lors du démarrage du dashboard avec diagnostic automatique
- **Mesurable** : 100% des erreurs critiques capturées, affichage immédiat, diagnostic dans 80% des cas
- **Atteignable** : Try/except autour de l'initialisation des composants, analyse des messages d'erreur
- **Réaliste** : Les erreurs sont loggées et peuvent être capturées et analysées
- **Temporel** : Disponible via endpoint /api/ai-healing/startup-issues, stockage dans DB

#### Objectif 3.2 : Vérification Port Mirroring
- **Spécifique** : Vérifier que le port mirroring est actif sur le switch
- **Mesurable** : Vérification en < 5 secondes, détection de 100% des problèmes de mirroring
- **Atteignable** : Vérification via API TP-Link ou détection de trafic sur eth0
- **Réaliste** : Le trafic mirroiré est visible sur l'interface
- **Temporel** : Disponible via endpoint /api/mirror/status

### 4. Visualisation et Analyse

#### Objectif 4.1 : Historique des Alertes
- **Spécifique** : Afficher les 50 dernières alertes avec leurs détails (signature, IPs, timestamp, sévérité)
- **Mesurable** : Chargement en < 2 secondes, affichage de 50 alertes maximum, stockage dans DB
- **Atteignable** : Lecture des logs Suricata récents, insertion en DB
- **Réaliste** : Les logs sont accessibles rapidement
- **Temporel** : Disponible via endpoint /api/alerts/recent

#### Objectif 4.2 : Visualisation Réseau Tailscale (Graphe Interactif)
- **Spécifique** : Générer un graphe HTML interactif avec Pyvis montrant tous les nœuds Tailscale, leurs connexions, latence, et liens vers console
- **Mesurable** : Génération du graphe en < 10 secondes, tous les nœuds visibles, taille des nœuds proportionnelle à la latence, nœuds stockés en DB
- **Atteignable** : Utilisation de Pyvis + NetworkX pour créer le graphe interactif
- **Réaliste** : Pyvis génère des graphes HTML interactifs rapidement
- **Temporel** : Disponible via endpoint /api/tailscale/visualize ou intégré dans le dashboard

#### Objectif 4.3 : Statistiques Trafic
- **Spécifique** : Afficher le débit réseau (Rx/Tx) et le nombre de paquets avec formatage lisible
- **Mesurable** : Mise à jour toutes les 5 secondes, formatage en Gbps/Mbps/Kbps
- **Atteignable** : Calcul basé sur psutil.net_io_counters()
- **Réaliste** : Les statistiques réseau sont disponibles en temps réel
- **Temporel** : Disponible via endpoint /api/network/stats

#### Objectif 4.4 : Liste des Services Systemd
- **Spécifique** : Afficher la liste de tous les services systemd (Suricata, Vector, ids-dashboard) avec leur statut (active/inactive, enabled/disabled)
- **Mesurable** : Mise à jour toutes les 10 secondes, 100% des services listés, statut stocké en DB
- **Atteignable** : Vérification via systemctl is-active et systemctl is-enabled
- **Réaliste** : systemctl répond rapidement
- **Temporel** : Disponible via endpoint /api/services/list

#### Objectif 4.5 : Liste des Index Elasticsearch
- **Spécifique** : Afficher la liste des index Elasticsearch avec leur nom, taille, nombre de documents, date de création
- **Mesurable** : Chargement en < 3 secondes, tous les index affichés, synchronisation avec DB toutes les heures
- **Atteignable** : Requête API Elasticsearch /_cat/indices, stockage en DB
- **Réaliste** : API Elasticsearch retourne rapidement la liste
- **Temporel** : Disponible via endpoint /api/elasticsearch/indices

### 5. Gestion du Réseau Tailscale

#### Objectif 5.1 : Ajout de Nœud Tailscale
- **Spécifique** : Ajouter un nouveau nœud au réseau Tailscale depuis le dashboard en fournissant hostname, IP (optionnel), et tags
- **Mesurable** : Ajout réussi en < 30 secondes, nœud visible dans le tailnet immédiatement, nœud stocké en DB
- **Atteignable** : Création automatique de clé d'authentification + déploiement Tailscale sur le nœud
- **Réaliste** : API Tailscale permet la création de clés et l'ajout de nœuds
- **Temporel** : Disponible via endpoint /api/tailscale/add-node

#### Objectif 5.2 : Création Clé d'Authentification
- **Spécifique** : Créer une clé d'authentification Tailscale réutilisable ou éphémère depuis le dashboard
- **Mesurable** : Création en < 5 secondes, clé retournée immédiatement
- **Atteignable** : Appel API Tailscale /api/v2/tailnet/{tailnet}/keys
- **Réaliste** : API Tailscale supporte la création de clés
- **Temporel** : Disponible via endpoint /api/setup/tailnet/create-key

#### Objectif 5.3 : Liste des Nœuds Tailscale
- **Spécifique** : Afficher tous les nœuds Tailscale avec statut (online/offline), dernière connexion, tags, IP
- **Mesurable** : Mise à jour toutes les 30 secondes, 100% des nœuds affichés, synchronisation avec DB
- **Atteignable** : Appel API Tailscale pour lister les devices, stockage en DB
- **Réaliste** : API retourne rapidement la liste
- **Temporel** : Disponible via endpoint /api/tailscale/nodes

### 6. Gestion Elasticsearch/OpenSearch

#### Objectif 6.1 : Liste des Index
- **Spécifique** : Afficher la liste des index Elasticsearch avec nom, taille, nombre de documents, date de création
- **Mesurable** : Chargement en < 3 secondes, tous les index affichés avec détails, synchronisation DB
- **Atteignable** : Requête API Elasticsearch /_cat/indices avec format détaillé, stockage en DB
- **Réaliste** : API Elasticsearch retourne ces informations rapidement
- **Temporel** : Disponible via endpoint /api/elasticsearch/indices

#### Objectif 6.2 : Statistiques des Index
- **Spécifique** : Afficher les statistiques des index (taille totale, nombre total de documents, indices par jour)
- **Mesurable** : Calcul en < 2 secondes, statistiques précises
- **Atteignable** : Agrégation des données depuis /_cat/indices ou depuis la DB
- **Réaliste** : Les statistiques sont calculables rapidement
- **Temporel** : Disponible via endpoint /api/elasticsearch/index-stats

#### Objectif 6.3 : Création Index Pattern
- **Spécifique** : Permettre de créer ou modifier des index patterns pour organiser les données
- **Mesurable** : Création en < 5 secondes, pattern appliqué immédiatement, stockage en DB
- **Atteignable** : Configuration via API Elasticsearch ou interface Kibana/OpenSearch Dashboards, stockage en DB
- **Réaliste** : Les index patterns sont configurables via API
- **Temporel** : Disponible via endpoint /api/elasticsearch/create-index-pattern

#### Objectif 6.4 : Création Dashboard Elasticsearch
- **Spécifique** : Créer un dashboard Elasticsearch/OpenSearch Dashboards depuis le dashboard IDS
- **Mesurable** : Création en < 10 secondes, dashboard accessible immédiatement, référence stockée en DB
- **Atteignable** : Utilisation de l'API OpenSearch Dashboards pour créer le dashboard
- **Réaliste** : L'API OpenSearch Dashboards permet la création programmatique
- **Temporel** : Disponible via endpoint /api/elasticsearch/create-dashboard

### 7. Alertes et Notifications

#### Objectif 7.1 : Alerte Visuelle LED
- **Spécifique** : Faire clignoter une LED rouge sur GPIO Pin 17 quand une alerte de sévérité 1 est détectée
- **Mesurable** : LED clignote dans les 100ms suivant la détection, 100% des alertes critiques déclenchent la LED
- **Atteignable** : Utilisation de gpiozero pour contrôler la LED
- **Réaliste** : GPIO est accessible sur Raspberry Pi
- **Temporel** : Fonctionnel dès qu'une LED est connectée

#### Objectif 7.2 : Classification par Sévérité
- **Spécifique** : Afficher les alertes avec un code couleur selon leur sévérité (rouge pour sévérité 1, jaune pour autres)
- **Mesurable** : 100% des alertes correctement classées, affichage immédiat
- **Atteignable** : Extraction du champ severity depuis les logs Suricata
- **Réaliste** : Les logs contiennent le champ severity
- **Temporel** : Disponible dès la première alerte

### 8. Accès et Disponibilité

#### Objectif 8.1 : Accès Réseau
- **Spécifique** : Rendre le dashboard accessible depuis n'importe quel appareil sur le réseau local
- **Mesurable** : Dashboard accessible sur http://IP:8080 depuis tous les appareils du réseau, 0% de downtime
- **Atteignable** : Binding sur 0.0.0.0:8080 permet l'accès réseau
- **Réaliste** : FastAPI supporte le binding réseau
- **Temporel** : Disponible dès le démarrage du service

#### Objectif 8.2 : Résilience
- **Spécifique** : Le dashboard reste accessible même si un composant (Suricata, Vector) plante
- **Mesurable** : Dashboard accessible 99.9% du temps, redémarrage automatique en < 10 secondes
- **Atteignable** : Service systemd avec Restart=always, gestion d'erreurs dans le code
- **Réaliste** : systemd gère les redémarrages automatiques
- **Temporel** : Fonctionnel dès la configuration du service systemd

### 9. Performance et Multithreading

#### Objectif 9.1 : Traitement Asynchrone des Opérations
- **Spécifique** : Traiter les opérations (lecture logs, requêtes API, calculs métriques) en parallèle sans bloquer l'interface
- **Mesurable** : Toutes les opérations s'exécutent simultanément, latence totale < 2 secondes pour toutes les mises à jour
- **Atteignable** : Utilisation d'asyncio pour opérations asynchrones, asyncio.to_thread pour opérations bloquantes
- **Réaliste** : Python asyncio permet le traitement parallèle efficace
- **Temporel** : Fonctionnel dès l'implémentation avec asyncio

#### Objectif 9.2 : Mises à Jour Concurrentes
- **Spécifique** : Mettre à jour toutes les sections du dashboard (alertes, métriques, statut pipeline) simultanément sans que l'une bloque l'autre
- **Mesurable** : Toutes les sections mises à jour en < 2 secondes total, aucune section ne bloque les autres
- **Atteignable** : Utilisation de asyncio.gather() pour exécuter toutes les requêtes en parallèle
- **Réaliste** : asyncio permet l'exécution concurrente de plusieurs coroutines
- **Temporel** : Disponible dès l'utilisation de asyncio dans le code

#### Objectif 9.3 : Streaming Non-Bloquant
- **Spécifique** : Streamer les alertes via WebSocket sans bloquer les autres opérations du dashboard
- **Mesurable** : Streaming continu sans interruption, autres endpoints REST restent accessibles
- **Atteignable** : WebSocket asynchrone avec asyncio, tâches séparées pour chaque opération
- **Réaliste** : FastAPI gère WebSocket de manière asynchrone
- **Temporel** : Fonctionnel dès l'implémentation WebSocket asynchrone

### 10. Déploiement Initial

#### Objectif 10.1 : Déploiement en Une Commande
- **Spécifique** : Déployer le dashboard en une seule commande Python avec juste IP, user SSH, password SSH, password sudo
- **Mesurable** : Déploiement réussi en < 5 minutes, 100% des cas si credentials valides
- **Atteignable** : Script Python automatisé avec SSH/SCP
- **Réaliste** : Les outils SSH/SCP permettent l'automatisation
- **Temporel** : Disponible via `python deploy.py`

#### Objectif 10.2 : Configuration Automatique au Premier Accès
- **Spécifique** : Configurer automatiquement tous les services (Suricata, Vector, Elasticsearch, Tailscale, OpenSearch) au premier accès au dashboard
- **Mesurable** : Configuration réussie dans 90% des cas, diagnostic automatique des erreurs dans 80% des cas
- **Atteignable** : Try/catch partout, analyse des erreurs, suggestions de résolution
- **Réaliste** : Les APIs permettent la configuration programmatique
- **Temporel** : Disponible dès le premier accès au dashboard

#### Objectif 10.3 : Diagnostic Automatique des Erreurs
- **Spécifique** : En cas d'erreur lors du déploiement, déterminer automatiquement la cause et afficher un diagnostic
- **Mesurable** : Diagnostic correct dans 80% des cas, suggestions de résolution dans 70% des cas
- **Atteignable** : Analyse des messages d'erreur, patterns d'erreurs connus, stockage en DB
- **Réaliste** : Les erreurs suivent des patterns reconnaissables
- **Temporel** : Disponible dès le premier déploiement

---

## 📋 Résumé des Inputs Utilisateur

### Inputs pour Script de Déploiement (`deploy.py`)
1. `pi_ip` - IP du Raspberry Pi
2. `pi_ssh_user` - Utilisateur SSH (défaut: `pi`)
3. `pi_ssh_password` - Mot de passe SSH
4. `pi_sudo_password` - Mot de passe sudo

### Inputs Obligatoires (Dashboard - Premier Accès)
1. `aws_access_key_id` - Clé AWS
2. `aws_secret_access_key` - Secret AWS
3. `tailscale_api_key` - Clé API Tailscale

### Inputs Optionnels (Dashboard)
4. `elasticsearch_username` - Si authentification activée
5. `elasticsearch_password` - Si authentification activée
6. `tailscale_oauth_client_id` - Pour OAuth (optionnel)
7. `tailscale_oauth_client_secret` - Pour OAuth (optionnel)

### Inputs pour Actions Spécifiques (Dashboard)
8. **Ajouter nœud** : hostname, IP (optionnel), tags (optionnel)
9. **Créer domaine OpenSearch** : nom du domaine (optionnel)
10. **Créer clé Tailscale** : réutilisable (oui/non), éphémère (oui/non), tags (optionnel)
11. **Créer index pattern** : nom, pattern, time_field
12. **Créer dashboard ES** : nom, description (optionnel)

---

## 🔧 Architecture Backend/Frontend

### Backend (FastAPI)

- **Base de données** : SQLite (dev) / PostgreSQL (prod) avec SQLAlchemy ORM
- **API REST** : Endpoints pour toutes les opérations (CRUD sur configs, services, etc.)
- **WebSocket** : Streaming des alertes en temps réel
- **Services** : Modules séparés pour Suricata, Vector, Elasticsearch, Tailscale, etc.
- **Gestion des erreurs** : Try/catch partout, diagnostic automatique, stockage en DB
- **Multithreading** : asyncio pour opérations asynchrones, asyncio.to_thread pour opérations bloquantes

### Frontend (React + TypeScript)

- **Affichage uniquement** : Pas de logique métier, tout passe par l'API REST
- **WebSocket Client** : Réception des alertes en temps réel
- **UI Moderne** : Tailwind CSS, Shadcn/UI, Lucide Icons
- **Thème Dark** : Glassmorphism, animations fluides
- **Charts** : Tremor.so pour visualisations

### Communication

- **REST API** : Toutes les opérations (config, services, déploiement)
- **WebSocket** : Streaming alertes temps réel
- **Base de données** : Tous les paramètres, configurations, métriques, alertes, logs

---

## 📊 Résumé des Objectifs SMART

| Use Case | Objectif SMART | Métrique | Délai | Inputs Utilisateur |
|----------|----------------|----------|-------|-------------------|
| Alertes temps réel | Latence < 1s | 100% alertes < 1s | Immédiat | Aucun |
| Statut pipeline | Mise à jour 5s | 100% précision | Immédiat | Aucun |
| Métriques système | Mise à jour 5s | Précision 1% | Immédiat | Aucun |
| Trafic réseau | Mise à jour 5s | Calcul débit | Immédiat | Aucun |
| Santé ES | Mise à jour 5s | Statut fiable | Immédiat | Aucun |
| Config Tailscale | Auto-détection | 100% si API key valide | < 5s | tailscale_api_key |
| Création OpenSearch | Un clic | 100% si AWS valide | 15-30 min | aws_access_key_id, aws_secret_access_key |
| Vérification infra | Test connectivité | < 10s | Immédiat | Aucun |
| Visualisation réseau | Graphe Pyvis | < 10s génération | Immédiat | tailscale_api_key |
| Ajout nœud | Ajout automatique | < 30s | Immédiat | hostname, IP (optionnel), tags (optionnel) |
| Liste services | Statut systemd | < 2s | Immédiat | Aucun |
| Liste index ES | Tous les index | < 3s | Immédiat | elasticsearch_username/password (si auth) |
| Création dashboard ES | Dashboard créé | < 10s | Immédiat | nom, description (optionnel) |
| LED alerte | Clignotement | < 100ms | Immédiat | Aucun |
| Accès réseau | Accessible | 99.9% uptime | Immédiat | Aucun |
| Multithreading | Opérations parallèles | < 2s toutes sections | Immédiat | Aucun |
| Déploiement initial | Une commande | < 5 min | Immédiat | pi_ip, pi_ssh_user, pi_ssh_password, pi_sudo_password |
| Config auto premier accès | Configuration complète | 90% succès | 15-30 min | aws_access_key_id, aws_secret_access_key, tailscale_api_key |
| Diagnostic erreurs | Cause déterminée | 80% précision | Immédiat | Aucun |
