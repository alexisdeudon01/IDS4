# 🔄 Pipeline IDS - Explication Simple

## Flux en 5 Étapes

```
┌─────────────┐
│  Internet   │
└──────┬──────┘
       │
       ▼
┌─────────────┐      ┌──────────────────┐
│   Routeur   │─────▶│ TP-Link Switch   │
└─────────────┘      │  Port Mirroring  │
                     │  Port 1 → Port 5 │
                     └──────┬────────────┘
                            │
                            │ (Copie du trafic)
                            ▼
                     ┌──────────────┐
                     │ Raspberry Pi │
                     │    eth0      │
                     └──────┬───────┘
                            │
                            ▼
                    ┌──────────────┐
                    │   Suricata   │ ◀─── Analyse les paquets
                    │   (IDS)      │      Détecte les menaces
                    └──────┬───────┘
                           │
                           │ (Alertes JSON)
                           ▼
                    ┌──────────────┐
                    │    Vector    │ ◀─── Collecte et enrichit
                    │  (Collector) │      les logs
                    └──────┬───────┘
                           │
                           │ (HTTP POST)
                           ▼
                    ┌──────────────┐
                    │  OpenSearch  │ ◀─── Stocke et indexe
                    │ /Elasticsearch│     les données
                    └──────┬───────┘
                           │
                           │ (API REST)
                           ▼
                    ┌──────────────┐
                    │   Dashboard  │ ◀─── Affiche et monitor
                    │   FastAPI    │      en temps réel
                    └──────────────┘
```

## Explication Détaillée

### 1️⃣ Capture (Port Mirroring)
- Le **switch** copie TOUT le trafic du routeur vers le Raspberry Pi
- Le Pi reçoit une **copie** du trafic (ne le modifie pas)
- Mode **promiscuous** : reçoit même les paquets non destinés au Pi

### 2️⃣ Inspection (Suricata)
- **Suricata** analyse chaque paquet en temps réel
- Compare avec des **règles de détection** (ET-Open)
- Génère des **alertes** si menace détectée
- Écrit dans `/var/log/suricata/eve.json`

### 3️⃣ Collecte (Vector)
- **Vector** lit les logs Suricata en continu
- **Enrichit** les données (géolocalisation, etc.)
- **Transforme** et normalise le format
- **Envoie** vers OpenSearch avec retry automatique

### 4️⃣ Stockage (OpenSearch)
- **OpenSearch** reçoit les données via HTTP
- **Indexe** par date (ex: `suricata-2024.02.04`)
- Permet la **recherche** et l'**analyse**
- **Rétention** configurable

### 5️⃣ Visualisation (Dashboard)
- **Dashboard FastAPI** lit les données
- **WebSocket** pour alertes en temps réel
- **REST API** pour historique et statistiques
- **Frontend** affiche graphiques et métriques

## Exemple Concret

**Scénario** : Un malware tente de se connecter

1. **Paquet malveillant** arrive sur le routeur
2. **Switch** copie vers le Pi (eth0)
3. **Suricata** détecte la signature du malware
4. **Alerte** générée avec sévérité 1 (critique)
5. **Vector** collecte et enrichit l'alerte
6. **OpenSearch** stocke l'alerte
7. **Dashboard** :
   - Reçoit l'alerte via WebSocket
   - Affiche dans l'interface
   - **LED rouge clignote** (GPIO Pin 17)
   - Enregistre dans l'historique

**Temps total** : < 1 seconde de la détection à l'affichage

## Avantages de cette Architecture

✅ **Passif** : N'interfère pas avec le trafic normal
✅ **Temps réel** : Détection et affichage instantanés
✅ **Scalable** : Peut gérer plusieurs capteurs
✅ **Persistant** : Toutes les alertes sont stockées
✅ **Visualisable** : Dashboard moderne et interactif

## Commandes Utiles

```bash
# Vérifier le pipeline
curl http://localhost:8080/api/pipeline/status

# Voir les alertes récentes
curl http://localhost:8080/api/alerts/recent

# Vérifier la santé OpenSearch
curl http://localhost:8080/api/elasticsearch/health

# Voir les stats réseau
curl http://localhost:8080/api/network/stats
```
