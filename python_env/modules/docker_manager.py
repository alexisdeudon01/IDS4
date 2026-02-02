import docker
import logging
import time
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(processName)s - %(levelname)s - %(message)s')

class DockerManager:
    """
    Gère le cycle de vie des conteneurs Docker et Docker Compose.
    """
    def __init__(self, config_manager, shared_state):
        self.config = config_manager
        self.shared_state = shared_state
        self.docker_compose_path = "docker/docker-compose.yml"
        self.client = docker.from_env()

    def _check_docker_daemon(self):
        """
        Vérifie si le démon Docker est en cours d'exécution.
        """
        try:
            self.client.ping()
            logging.info("Le démon Docker est en cours d'exécution.")
            return True
        except Exception as e:
            logging.error(f"Le démon Docker n'est pas accessible : {e}")
            self.shared_state['last_error'] = f"Docker daemon not accessible: {e}"
            return False

    def _run_docker_compose_command(self, command, detach=False):
        """
        Exécute une commande docker-compose.
        """
        if not os.path.exists(self.docker_compose_path):
            logging.error(f"Fichier docker-compose.yml non trouvé à : {self.docker_compose_path}")
            self.shared_state['last_error'] = f"docker-compose.yml not found: {self.docker_compose_path}"
            return False

        cmd = f"docker compose -f {self.docker_compose_path} {command}"
        if detach:
            cmd += " -d"
        
        logging.info(f"Exécution de la commande Docker Compose : {cmd}")
        try:
            # Utiliser subprocess pour exécuter docker-compose car le client Python Docker ne gère pas compose directement
            import subprocess
            result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
            logging.info(f"Sortie Docker Compose :\n{result.stdout}")
            if result.stderr:
                logging.warning(f"Erreurs/Avertissements Docker Compose :\n{result.stderr}")
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Échec de la commande Docker Compose '{command}' : {e.stderr}")
            self.shared_state['last_error'] = f"Docker Compose failed: {e.stderr}"
            return False
        except FileNotFoundError:
            logging.error("La commande 'docker compose' n'a pas été trouvée. Assurez-vous que Docker Compose est installé.")
            self.shared_state['last_error'] = "Docker Compose command not found."
            return False
        except Exception as e:
            logging.error(f"Erreur inattendue lors de l'exécution de Docker Compose : {e}")
            self.shared_state['last_error'] = f"Unexpected Docker Compose error: {e}"
            return False

    def prepare_docker_stack(self):
        """
        Construit et démarre la pile Docker Compose.
        """
        if not self._check_docker_daemon():
            return False
        
        logging.info("Préparation de la pile Docker...")
        if not self._run_docker_compose_command("build"):
            return False
        if not self._run_docker_compose_command("up", detach=True):
            return False
        
        logging.info("Pile Docker démarrée avec succès.")
        return True

    def stop_docker_stack(self):
        """
        Arrête et supprime la pile Docker Compose.
        """
        if not self._check_docker_daemon():
            return False
        
        logging.info("Arrêt de la pile Docker...")
        if not self._run_docker_compose_command("down"):
            return False
        
        logging.info("Pile Docker arrêtée et supprimée.")
        return True

    def check_stack_health(self):
        """
        Vérifie la santé des services Docker.
        """
        if not self._check_docker_daemon():
            return False
        
        try:
            # Obtenir la liste des services définis dans docker-compose.yml
            # Pour cela, il faudrait parser le fichier ou utiliser 'docker compose ps --services'
            # Pour l'instant, nous allons vérifier si les conteneurs sont en cours d'exécution.
            
            # Une approche plus robuste serait de vérifier l'état de santé de chaque service
            # via 'docker inspect <container_id>' et son Healthcheck si défini.
            
            # Pour ce POC, nous allons simplement vérifier si les conteneurs sont démarrés.
            required_services = ["vector", "redis", "prometheus", "grafana"] # Basé sur le prompt
            all_healthy = True
            for service_name in required_services:
                try:
                    container = self.client.containers.get(f"oi-{service_name}-1") # Nom par défaut de docker compose
                    if container.status != 'running':
                        logging.warning(f"Le service Docker '{service_name}' n'est pas en cours d'exécution. Statut: {container.status}")
                        all_healthy = False
                        break
                    else:
                        logging.info(f"Le service Docker '{service_name}' est en cours d'exécution.")
                except docker.errors.NotFound: # Correction: docker.errors.NotFound est la bonne façon d'accéder à l'exception
                    logging.warning(f"Le conteneur pour le service Docker '{service_name}' n'a pas été trouvé.")
                    all_healthy = False
                    break
                except Exception as e:
                    logging.error(f"Erreur lors de la vérification du service Docker '{service_name}' : {e}")
                    all_healthy = False
                    break
            
            self.shared_state['docker_healthy'] = all_healthy
            if not all_healthy:
                self.shared_state['last_error'] = "Docker stack not healthy."
            return all_healthy

        except Exception as e:
            logging.error(f"Erreur lors de la vérification de la santé de la pile Docker : {e}")
            self.shared_state['docker_healthy'] = False
            self.shared_state['last_error'] = f"Docker health check error: {e}"
            return False

# Exemple d'utilisation (pour les tests)
if __name__ == "__main__":
    from config_manager import ConfigManager
    import multiprocessing
    
    # Créer un fichier config.yaml temporaire pour le test
    temp_config_content = """
    docker:
      vector_cpu: 1.0
      vector_ram_mb: 1024
      redis_cpu: 0.5
      redis_ram_mb: 512
      prometheus_cpu: 0.5
      prometheus_ram_mb: 512
      grafana_cpu: 0.5
      grafana_ram_mb: 512
    """
    with open('temp_config.yaml', 'w') as f:
        f.write(temp_config_content)

    # Créer un docker-compose.yml temporaire pour le test
    temp_docker_compose_content = """
version: '3.8'
services:
  test_service:
    image: alpine/git
    command: ["sh", "-c", "echo 'Hello from Docker!' && sleep 30"]
    deploy:
      resources:
        limits:
          cpus: '0.1'
          memory: 64M
"""
    os.makedirs('docker', exist_ok=True)
    with open('docker/docker-compose.yml', 'w') as f:
        f.write(temp_docker_compose_content)

    try:
        config_mgr = ConfigManager(config_path='temp_config.yaml')
        manager = multiprocessing.Manager()
        shared_state = manager.dict({
            'docker_healthy': False,
            'last_error': ''
        })

        docker_mgr = DockerManager(config_mgr, shared_state)

        print("\nTest de préparation de la pile Docker...")
        if docker_mgr.prepare_docker_stack():
            print("Pile Docker préparée. Attente de 5 secondes pour la santé...")
            time.sleep(5)
            print(f"Santé de la pile Docker : {docker_mgr.check_stack_health()}")
        
        print("\nTest d'arrêt de la pile Docker...")
        docker_mgr.stop_docker_stack()

    except Exception as e:
        logging.error(f"Erreur lors du test de DockerManager: {e}")
    finally:
        if os.path.exists('temp_config.yaml'):
            os.remove('temp_config.yaml')
        if os.path.exists('docker/docker-compose.yml'):
            os.remove('docker/docker-compose.yml')
        if os.path.exists('docker'):
            os.rmdir('docker')
