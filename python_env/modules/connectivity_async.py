import asyncio
import uvloop
import socket
import ssl
import time
import logging
import aiohttp # Nécessaire pour les requêtes HTTP asynchrones

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(processName)s - %(levelname)s - %(message)s')

class ConnectivityAsync:
    """
    Gère les vérifications de connectivité réseau asynchrones (DNS, TLS, OpenSearch).
    """
    def __init__(self, shared_state, config_manager):
        self.shared_state = shared_state
        self.config = config_manager
        self.opensearch_endpoint = self.config.get('aws.opensearch_endpoint')
        self.aws_region = self.config.get('aws.region')
        self.redis_host = self.config.get('redis.host')
        self.redis_port = self.config.get('redis.port')
        self.max_retries = 5
        self.initial_backoff = 1 # secondes

        # Configurer uvloop comme boucle d'événements par défaut
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    async def _retry_operation(self, func, *args, **kwargs):
        """
        Exécute une fonction avec réessais et backoff exponentiel.
        """
        retries = 0
        while retries < self.max_retries:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                retries += 1
                if retries >= self.max_retries:
                    raise
                sleep_time = self.initial_backoff * (2 ** retries)
                logging.warning(f"Opération '{func.__name__}' échouée ({e}). Réessai dans {sleep_time:.2f}s (tentative {retries}/{self.max_retries}).")
                await asyncio.sleep(sleep_time)

    async def check_dns_resolution(self, hostname):
        """
        Vérifie la résolution DNS d'un hostname.
        """
        try:
            await asyncio.get_event_loop().getaddrinfo(hostname, None)
            logging.info(f"Résolution DNS réussie pour {hostname}")
            return True
        except socket.gaierror as e:
            logging.error(f"Échec de la résolution DNS pour {hostname}: {e}")
            raise

    async def check_tls_handshake(self, hostname, port=443):
        """
        Vérifie la négociation TLS avec un hôte.
        """
        try:
            ssl_context = ssl.create_default_context()
            reader, writer = await asyncio.open_connection(hostname, port, ssl=ssl_context)
            writer.close()
            await writer.wait_closed() # Correction: wait_closed est sur le writer
            logging.info(f"Négociation TLS réussie avec {hostname}:{port}")
            return True
        except (ConnectionRefusedError, socket.timeout, ssl.SSLError, OSError) as e:
            logging.error(f"Échec de la négociation TLS avec {hostname}:{port}: {e}")
            raise

    async def check_opensearch_bulk_test(self):
        """
        Effectue un test de connectivité à l'API _bulk d'OpenSearch.
        """
        if not self.opensearch_endpoint:
            logging.warning("Endpoint OpenSearch non configuré, impossible de tester la connectivité.")
            self.shared_state['aws_ready'] = False
            return False

        # L'endpoint OpenSearch est généralement au format https://<domain-id>.<region>.es.amazonaws.com
        # Nous devons extraire le hostname pour les vérifications DNS/TLS
        try:
            opensearch_url = self.opensearch_endpoint.rstrip('/') + '/_cluster/health' # Utiliser une API légère pour le test
            
            # Pour une vraie implémentation, vous auriez besoin d'un client AWS SigV4 pour aiohttp
            # ou d'un client OpenSearch asynchrone. Pour ce POC, nous allons simuler.
            # Une implémentation réelle nécessiterait des en-têtes d'authentification AWS.
            
            async with aiohttp.ClientSession() as session:
                async with session.get(opensearch_url, timeout=5) as response:
                    if response.status == 200:
                        logging.info(f"Test OpenSearch réussi. Statut: {response.status}")
                        self.shared_state['aws_ready'] = True
                        return True
                    else:
                        logging.warning(f"Test OpenSearch échoué. Statut: {response.status}")
                        self.shared_state['aws_ready'] = False
                        self.shared_state['last_error'] = f"OpenSearch health check failed: {response.status}"
                        return False
        except aiohttp.ClientError as e:
            logging.error(f"Erreur client HTTP lors du test OpenSearch: {e}")
            self.shared_state['aws_ready'] = False
            self.shared_state['last_error'] = f"OpenSearch HTTP client error: {e}"
            raise
        except Exception as e:
            logging.error(f"Erreur inattendue lors du test OpenSearch: {e}")
            self.shared_state['aws_ready'] = False
            self.shared_state['last_error'] = f"OpenSearch test error: {e}"
            raise

    async def check_redis_connectivity(self):
        """
        Vérifie la connectivité à Redis.
        """
        try:
            reader, writer = await asyncio.open_connection(self.redis_host, self.redis_port)
            writer.close()
            await writer.wait_closed() # Correction: wait_closed est sur le writer
            logging.info(f"Connectivité Redis réussie à {self.redis_host}:{self.redis_port}")
            self.shared_state['redis_ready'] = True # Ajout d'un état redis_ready
            return True
        except (ConnectionRefusedError, socket.timeout, OSError) as e:
            logging.error(f"Échec de la connectivité Redis à {self.redis_host}:{self.redis_port}: {e}")
            self.shared_state['redis_ready'] = False
            self.shared_state['last_error'] = f"Redis connectivity error: {e}"
            raise

    async def run_connectivity_checks(self):
        """
        Exécute toutes les vérifications de connectivité en parallèle.
        """
        logging.info("Processus de Connectivité (ASYNC) démarré.")
        while True:
            try:
                # Extraire le hostname de l'endpoint OpenSearch
                opensearch_hostname = None
                if self.opensearch_endpoint:
                    opensearch_hostname = self.opensearch_endpoint.split('//')[-1].split('/')[0].split(':')[0]

                tasks = []
                if opensearch_hostname:
                    tasks.append(self._retry_operation(self.check_dns_resolution, opensearch_hostname))
                    tasks.append(self._retry_operation(self.check_tls_handshake, opensearch_hostname))
                    tasks.append(self._retry_operation(self.check_opensearch_bulk_test))
                
                tasks.append(self._retry_operation(self.check_redis_connectivity))

                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Mettre à jour l'état global du pipeline
                pipeline_ok = all(r is True for r in results if not isinstance(r, Exception))
                self.shared_state['pipeline_ok'] = pipeline_ok
                if not pipeline_ok:
                    logging.warning("Certaines vérifications de connectivité ont échoué.")
                else:
                    logging.info("Toutes les vérifications de connectivité sont OK.")

            except Exception as e:
                logging.error(f"Erreur critique dans le processus de connectivité: {e}")
                self.shared_state['pipeline_ok'] = False
                self.shared_state['last_error'] = f"Connectivity process error: {e}"
            
            # S'assurer que l'intervalle est un nombre
            interval = self.config.get('connectivity_check_interval', 10)
            if not isinstance(interval, (int, float)):
                logging.warning(f"connectivity_check_interval dans config.yaml n'est pas un nombre. Utilisation de la valeur par défaut (10s).")
                interval = 10
            await asyncio.sleep(interval) # Vérifier toutes les 10 secondes

    def run(self):
        """
        Point d'entrée pour le processus de connectivité.
        """
        asyncio.run(self.run_connectivity_checks())

# Exemple d'utilisation (pour les tests)
if __name__ == "__main__":
    import os
    from config_manager import ConfigManager
    import multiprocessing

    # Créer un fichier config.yaml temporaire pour le test
    temp_config_content = """
    aws:
      opensearch_endpoint: "https://your-opensearch-domain.eu-west-1.es.amazonaws.com" # Remplacez par un endpoint valide ou invalide pour tester
      region: "eu-west-1"
    redis:
      host: "localhost"
      port: 6379
    connectivity_check_interval: 5
    """
    with open('temp_config.yaml', 'w') as f:
        f.write(temp_config_content)

    try:
        config_mgr = ConfigManager(config_path='temp_config.yaml')
        manager = multiprocessing.Manager()
        shared_state = manager.dict({
            'aws_ready': False,
            'redis_ready': False,
            'pipeline_ok': False,
            'last_error': ''
        })

        connectivity_checker = ConnectivityAsync(shared_state, config_mgr)
        
        # Démarrer le processus de connectivité
        process = multiprocessing.Process(target=connectivity_checker.run, name="ConnectivityProcess")
        process.start()
        
        for _ in range(3): # Exécuter pendant 15 secondes (3 * 5s d'intervalle)
            # S'assurer que l'intervalle est un nombre pour le test
            test_interval = config_mgr.get('connectivity_check_interval', 5)
            if not isinstance(test_interval, (int, float)):
                test_interval = 5
            time.sleep(test_interval + 1) # Attendre un peu plus que l'intervalle
            print(f"\nÉtat partagé - AWS Ready: {shared_state['aws_ready']}, Redis Ready: {shared_state['redis_ready']}, Pipeline OK: {shared_state['pipeline_ok']}, Last Error: {shared_state['last_error']}")
        
        process.terminate()
        process.join()

    except Exception as e:
        logging.error(f"Erreur lors du test de ConnectivityAsync: {e}")
    finally:
        if os.path.exists('temp_config.yaml'):
            os.remove('temp_config.yaml')
