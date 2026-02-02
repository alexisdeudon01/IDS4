import logging
import os
import subprocess
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(processName)s - %(levelname)s - %(message)s')

class VectorManager:
    """
    Gère la configuration et le cycle de vie de Vector.
    """
    def __init__(self, config_manager, shared_state):
        self.config = config_manager
        self.shared_state = shared_state
        self.vector_config_path = self.config.get('vector.config_path', 'vector/vector.toml')
        self.log_read_path = self.config.get('vector.log_read_path', '/mnt/ram_logs/eve.json')
        self.opensearch_endpoint = self.config.get('aws.opensearch_endpoint')
        self.aws_region = self.config.get('aws.region')
        self.redis_host = self.config.get('redis.host')
        self.redis_port = self.config.get('redis.port')

    def generate_vector_config(self):
        """
        Génère le fichier de configuration vector.toml basé sur les paramètres du projet.
        """
        logging.info(f"Génération du fichier de configuration Vector à : {self.vector_config_path}")

        # Assurez-vous que le répertoire existe
        os.makedirs(os.path.dirname(self.vector_config_path), exist_ok=True)

        vector_config_content = f"""
# Configuration Vector pour IDS2 SOC Pipeline

# Source : Lecture des logs Suricata
[sources.suricata_logs]
type = "file"
include = ["{self.log_read_path}"]
read_from = "beginning"
fingerprint_bytes = 1024 # Pour gérer les rotations de fichiers

# Transformation : Parser les logs JSON de Suricata
[transforms.parse_json]
type = "remap"
inputs = ["suricata_logs"]
source = '''
  . = parse_json!(.message)
  # Assurez-vous que les champs sont conformes à ECS si possible
  # Exemple de renommage/enrichissement pour ECS
  .event.kind = "event"
  .event.category = "network"
  .event.type = "connection" # Ou "alert", "flow", etc. selon le type d'événement Suricata
  .source.ip = .src_ip
  .destination.ip = .dest_ip
  .source.port = .src_port
  .destination.port = .dest_port
  .network.protocol = .proto
  del(.src_ip)
  del(.dest_ip)
  del(.src_port)
  del(.dest_port)
  del(.proto)
'''

# Tampon disque pour Vector (obligatoire pour la résilience)
[buffers.disk_buffer]
type = "disk"
path = "/var/lib/vector/buffer" # Chemin persistant pour le tampon disque
max_size = 100 GiB # Taille maximale du tampon disque
when_full = "block"

# Sink : Envoi à Redis comme fallback
[sinks.redis_fallback]
type = "redis"
inputs = ["parse_json"]
address = "{self.redis_host}:{self.redis_port}"
key = "vector_logs"
encoding = "json"
batch.max_events = 1000 # Taille de lot optimisée pour Pi
batch.timeout_secs = 5
healthcheck.enabled = true
# Utilise le tampon disque si Redis est lent/indisponible
buffer.type = "disk"
buffer.path = "/var/lib/vector/redis_buffer"
buffer.max_size = 10 GiB

# Sink : Envoi à AWS OpenSearch
[sinks.opensearch_sink]
type = "elasticsearch"
inputs = ["parse_json"]
endpoint = "{self.opensearch_endpoint}"
index = "ids2-logs-%Y.%m.%d" # Index quotidien
auth.strategy = "aws"
auth.region = "{self.aws_region}"
# auth.access_key_id = "$AWS_ACCESS_KEY_ID" # Peut être configuré via variables d'environnement Docker
# auth.secret_access_key = "$AWS_SECRET_ACCESS_KEY"
# auth.session_token = "$AWS_SESSION_TOKEN"
compression = "gzip"
batch.max_events = 500 # Taille de lot optimisée pour Pi
batch.timeout_secs = 2
request.timeout_secs = 30
healthcheck.enabled = true
# Utilise le tampon disque si OpenSearch est lent/indisponible
buffer.type = "disk"
buffer.path = "/var/lib/vector/opensearch_buffer"
buffer.max_size = 50 GiB

# Routes pour la résilience :
# Si OpenSearch est prêt, envoie directement. Sinon, utilise Redis.
# Cette logique est plus complexe à gérer directement dans vector.toml sans conditionnalité avancée.
# L'agent Python gérera la logique de basculement entre les sinks si nécessaire,
# ou Vector utilisera ses propres mécanismes de buffer et de retry.
# Pour l'instant, les deux sinks sont configurés avec des buffers disques.
"""
        try:
            with open(self.vector_config_path, 'w') as f:
                f.write(vector_config_content)
            logging.info("Fichier de configuration Vector généré avec succès.")
            return True
        except IOError as e:
            logging.error(f"Erreur lors de l'écriture du fichier de configuration Vector : {e}")
            self.shared_state['last_error'] = f"Vector config write error: {e}"
            return False

    def check_vector_health(self):
        """
        Vérifie la santé de Vector (via Docker).
        """
        # La santé de Vector est vérifiée par DockerManager.check_stack_health
        # Ici, nous pourrions ajouter des vérifications spécifiques à Vector si nécessaire,
        # par exemple en interrogeant son API de métriques si elle est exposée.
        # Pour l'instant, nous nous basons sur l'état du conteneur Docker.
        if self.shared_state.get('docker_healthy', False):
            logging.info("Le conteneur Vector est sain (selon DockerManager).")
            self.shared_state['vector_healthy'] = True
            return True
        else:
            logging.warning("Le conteneur Vector n'est pas sain.")
            self.shared_state['vector_healthy'] = False
            self.shared_state['last_error'] = "Vector container not healthy."
            return False

# Exemple d'utilisation (pour les tests)
if __name__ == "__main__":
    from config_manager import ConfigManager
    import multiprocessing
    
    # Créer un fichier config.yaml temporaire pour le test
    temp_config_content = """
    vector:
      config_path: "vector/vector.toml"
      log_read_path: "/tmp/eve.json"
    aws:
      opensearch_endpoint: "https://your-opensearch-domain.eu-west-1.es.amazonaws.com"
      region: "eu-west-1"
    redis:
      host: "localhost"
      port: 6379
    """
    with open('temp_config.yaml', 'w') as f:
        f.write(temp_config_content)

    try:
        config_mgr = ConfigManager(config_path='temp_config.yaml')
        manager = multiprocessing.Manager()
        shared_state = manager.dict({
            'docker_healthy': False,
            'vector_healthy': False,
            'last_error': ''
        })

        vector_mgr = VectorManager(config_mgr, shared_state)

        print("\nTest de génération de la configuration Vector...")
        if vector_mgr.generate_vector_config():
            print(f"Contenu de {vector_mgr.vector_config_path} :\n")
            with open(vector_mgr.vector_config_path, 'r') as f:
                print(f.read())
        
        print("\nTest de vérification de la santé de Vector (simulé)...")
        shared_state['docker_healthy'] = True # Simuler un Docker sain
        print(f"Santé de Vector : {vector_mgr.check_vector_health()}")
        shared_state['docker_healthy'] = False # Simuler un Docker non sain
        print(f"Santé de Vector : {vector_mgr.check_vector_health()}")

    except Exception as e:
        logging.error(f"Erreur lors du test de VectorManager: {e}")
    finally:
        if os.path.exists('temp_config.yaml'):
            os.remove('temp_config.yaml')
        if os.path.exists('vector/vector.toml'):
            os.remove('vector/vector.toml')
        if os.path.exists('vector'):
            os.rmdir('vector')
