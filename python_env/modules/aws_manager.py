import boto3
import json
import time
import logging
import os
import multiprocessing
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError
from opensearchpy import OpenSearch, RequestsHttpConnection
from opensearchpy.exceptions import ConnectionError as OpenSearchConnectionError
from requests_aws4auth import AWS4Auth

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(processName)s - %(levelname)s - %(message)s')

class AWSManager:
    """
    Gère les interactions avec les services AWS, notamment l'envoi de logs à OpenSearch.
    """
    def __init__(self, config_manager, shared_state):
        self.config = config_manager
        self.shared_state = shared_state
        self.opensearch_endpoint = self.config.get('aws.opensearch_endpoint')
        self.aws_region = self.config.get('aws.region')
        self.aws_profile = self.config.get('aws.profile')
        self.opensearch_domain_name = self.config.get('aws.domain_name')
        
        if not self.aws_region:
            logging.error("La région AWS n'est pas configurée dans config.yaml.")
            raise ValueError("Configuration AWS incomplète : région manquante.")

        self.session = self._get_aws_session()
        self.opensearch_client = self.session.client('opensearch', region_name=self.aws_region)

    def _get_aws_session(self):
        """
        Crée une session AWS en utilisant le profil ou les identifiants spécifiés.
        """
        aws_access_key_id = self.config.get('aws.access_key_id')
        aws_secret_access_key = self.config.get('aws.secret_access_key')

        try:
            if aws_access_key_id and aws_secret_access_key:
                return boto3.Session(
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key,
                    region_name=self.aws_region
                )
            elif self.aws_profile:
                return boto3.Session(profile_name=self.aws_profile, region_name=self.aws_region)
            else:
                logging.warning("Aucun identifiant AWS ou profil spécifié. Tentative d'utiliser les identifiants par défaut (variables d'environnement, rôle IAM).")
                return boto3.Session(region_name=self.aws_region)
        except (NoCredentialsError, PartialCredentialsError) as e:
            logging.error(f"Erreur d'authentification AWS : {e}. Vérifiez vos identifiants et le profil '{self.aws_profile}'.")
            raise
        except Exception as e:
            logging.error(f"Erreur lors de la création de la session AWS : {e}")
            raise

    def send_bulk_to_opensearch(self, logs, index_name_prefix="suricata-", max_retries=5, initial_backoff=1):
        """
        Envoie une liste de logs à AWS OpenSearch en utilisant l'API _bulk.
        Gère les réessais avec backoff exponentiel.
        Les logs doivent être au format ECS-compliant.
        """
        if not self.opensearch_endpoint:
            logging.error("Endpoint OpenSearch non disponible, impossible d'envoyer les logs.")
            self.shared_state['aws_ready'] = False
            self.shared_state['last_error'] = "OpenSearch endpoint not configured."
            return False

        if not logs:
            return True

        bulk_data = []
        for log in logs:
            if isinstance(log, dict):
                # Utiliser le pattern d'index défini dans config.yaml
                index_pattern = self.config.get('vector.index_pattern', index_name_prefix + "%Y.%m.%d")
                current_index_name = time.strftime(index_pattern)
                bulk_data.append(json.dumps({"index": {"_index": current_index_name}}))
                bulk_data.append(json.dumps(log))
            else:
                logging.warning(f"Log ignoré car non au format dictionnaire: {log}")
                continue
        
        if not bulk_data:
            return True # Aucun log valide à envoyer

        payload = "\n".join(bulk_data) + "\n"
        
        retries = 0
        while retries < max_retries:
            try:
                awsauth = AWS4Auth(
                    self.session.get_credentials().access_key,
                    self.session.get_credentials().secret_key,
                    self.aws_region,
                    'es',
                    session_token=self.session.get_credentials().token
                )

                client = OpenSearch(
                    hosts=[{'host': self.opensearch_endpoint.split('//')[-1].split(':')[0], 'port': 443}],
                    http_auth=awsauth,
                    use_ssl=True,
                    verify_certs=True,
                    connection_class=RequestsHttpConnection
                )
                
                logging.info(f"Tentative d'envoi de {len(logs)} logs à OpenSearch (tentative {retries + 1}/{max_retries})...")
                response = client.bulk(body=payload)

                if response and not response.get('errors'):
                    self.shared_state['aws_ready'] = True
                    logging.info(f"Logs envoyés avec succès à OpenSearch.")
                    return True
                else:
                    error_details = json.dumps(response, indent=2)
                    logging.error(f"Erreur lors de l'envoi en masse à OpenSearch: {error_details}")
                    self.shared_state['aws_ready'] = False
                    self.shared_state['last_error'] = f"OpenSearch bulk error: {error_details}"
                    return False

            except OpenSearchConnectionError as e:
                logging.error(f"Erreur de connexion OpenSearch : {e}")
                self.shared_state['aws_ready'] = False
                self.shared_state['last_error'] = f"OpenSearch connection error: {e}"
            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code")
                logging.error(f"Erreur Client AWS lors de l'envoi à OpenSearch ({error_code}): {e}")
                self.shared_state['aws_ready'] = False
                self.shared_state['last_error'] = f"AWS ClientError: {error_code}"
            except Exception as e:
                logging.error(f"Erreur inattendue lors de l'envoi à OpenSearch: {e}")
                self.shared_state['aws_ready'] = False
                self.shared_state['last_error'] = f"OpenSearch send error: {e}"

            retries += 1
            if retries < max_retries:
                sleep_time = initial_backoff * (2 ** retries)
                logging.warning(f"Réessai dans {sleep_time} secondes...")
                time.sleep(sleep_time)
        
        logging.error(f"Échec de l'envoi de logs à OpenSearch après {max_retries} tentatives.")
        return False

    def provision_opensearch_domain(self, max_wait_time=600):
        """
        Crée ou détecte un domaine OpenSearch et attend qu'il soit actif.
        Met à jour l'endpoint dans la configuration.
        """
        logging.info(f"Vérification ou création du domaine OpenSearch '{self.opensearch_domain_name}' dans la région '{self.aws_region}'...")
        
        try:
            response = self.opensearch_client.describe_domain(DomainName=self.opensearch_domain_name)
            domain_status = response['DomainStatus']
            logging.info(f"Domaine OpenSearch '{self.opensearch_domain_name}' détecté. Statut actuel : {domain_status.get('ProcessingState', 'N/A') if 'ProcessingState' in domain_status else domain_status.get('ServiceSoftwareOptions', {}).get('UpdateStatus', 'N/A')}")
            
            if domain_status.get('ProcessingState') == 'Active' or \
               (domain_status.get('ServiceSoftwareOptions') and domain_status['ServiceSoftwareOptions']['UpdateStatus'] == 'Completed'):
                self.opensearch_endpoint = domain_status['Endpoint']
                self.config.config['aws']['opensearch_endpoint'] = self.opensearch_endpoint
                logging.info(f"Domaine OpenSearch '{self.opensearch_domain_name}' est actif. Endpoint : {self.opensearch_endpoint}")
                self.shared_state['aws_ready'] = True
                return True
            
            logging.info(f"Attente de l'état 'Active' pour le domaine OpenSearch '{self.opensearch_domain_name}'...")
            start_time = time.time()
            while (time.time() - start_time) < max_wait_time:
                response = self.opensearch_client.describe_domain(DomainName=self.opensearch_domain_name)
                domain_status = response['DomainStatus']
                
                if domain_status.get('ProcessingState') == 'Active' or \
                   (domain_status.get('ServiceSoftwareOptions') and domain_status['ServiceSoftwareOptions']['UpdateStatus'] == 'Completed'):
                    self.opensearch_endpoint = domain_status['Endpoint']
                    self.config.config['aws']['opensearch_endpoint'] = self.opensearch_endpoint
                    logging.info(f"Domaine OpenSearch '{self.opensearch_domain_name}' est maintenant actif. Endpoint : {self.opensearch_endpoint}")
                    self.shared_state['aws_ready'] = True
                    return True
                
                logging.info(f"Domaine toujours en cours de provisionnement/mise à jour. Statut : {domain_status.get('ProcessingState', 'N/A') if 'ProcessingState' in domain_status else domain_status.get('ServiceSoftwareOptions', {}).get('UpdateStatus', 'N/A')}. Attente de 30 secondes...")
                time.sleep(30)
            
            logging.error(f"Le domaine OpenSearch '{self.opensearch_domain_name}' n'est pas devenu actif après {max_wait_time} secondes.")
            self.shared_state['aws_ready'] = False
            self.shared_state['last_error'] = f"OpenSearch domain not active after {max_wait_time}s."
            return False

        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                logging.info(f"Domaine OpenSearch '{self.opensearch_domain_name}' non trouvé. Création...")
                # Ici, vous définiriez les paramètres de création du domaine
                # Pour un POC, nous allons utiliser des valeurs minimales.
                # Une vraie implémentation nécessiterait une configuration plus détaillée (VPC, taille, etc.)
                try:
                    create_response = self.opensearch_client.create_domain(
                        DomainName=self.opensearch_domain_name,
                        ElasticsearchVersion='OpenSearch_1.3', # Ou une version plus récente
                        # NodeToNodeEncryptionOptions={'Enabled': True},
                        # EncryptionAtRestOptions={'Enabled': True},
                        # DomainEndpointOptions={'EnforceHTTPS': True, 'TLSSecurityPolicy': 'Policy-Min-TLS1-2-2019-07'},
                        # AccessPolicies='{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"AWS":["arn:aws:iam::YOUR_ACCOUNT_ID:root"]},"Action":"es:*","Resource":"arn:aws:es:YOUR_REGION:YOUR_ACCOUNT_ID:domain/YOUR_DOMAIN_NAME/*"}]}',
                        # VPCOptions={'SubnetIds': ['subnet-xxxxxxxxxxxxxxxxx'], 'SecurityGroupIds': ['sg-xxxxxxxxxxxxxxxxx']},
                        EBSOptions={
                            'EBSEnabled': True,
                            'VolumeType': 'gp2',
                            'VolumeSize': 10 # GB
                        },
                        ClusterConfig={
                            'InstanceType': 't3.small.search', # Type d'instance adapté pour un POC
                            'InstanceCount': 1
                        },
                        AdvancedOptions={
                            'rest.action.multi.allow_explicit_index': 'true'
                        }
                    )
                    logging.info(f"Demande de création du domaine OpenSearch '{self.opensearch_domain_name}' envoyée.")
                    return self.provision_opensearch_domain(max_wait_time) # Attendre l'activation après création
                except ClientError as create_e:
                    logging.error(f"Échec de la création du domaine OpenSearch : {create_e}")
                    self.shared_state['aws_ready'] = False
                    self.shared_state['last_error'] = f"OpenSearch domain creation failed: {create_e}"
                    return False
            else:
                logging.error(f"Erreur Client AWS lors de la description du domaine OpenSearch : {e}")
                self.shared_state['aws_ready'] = False
                self.shared_state['last_error'] = f"AWS ClientError: {e}"
                return False
        except Exception as e:
            logging.error(f"Erreur inattendue lors du provisioning OpenSearch : {e}")
            self.shared_state['aws_ready'] = False
            self.shared_state['last_error'] = f"OpenSearch provisioning error: {e}"
            return False

    def apply_index_template(self, template_name="ids2-suricata-template", index_pattern="suricata-*"):
        """
        Applique un modèle d'index ECS pour les logs Suricata dans OpenSearch.
        """
        if not self.opensearch_endpoint:
            logging.error("Endpoint OpenSearch non disponible, impossible d'appliquer le modèle d'index.")
            return False

        try:
            awsauth = AWS4Auth(
                self.session.get_credentials().access_key,
                self.session.get_credentials().secret_key,
                self.aws_region,
                'es',
                session_token=self.session.get_credentials().token
            )

            client = OpenSearch(
                hosts=[{'host': self.opensearch_endpoint.split('//')[-1].split(':')[0], 'port': 443}],
                http_auth=awsauth,
                use_ssl=True,
                verify_certs=True,
                connection_class=RequestsHttpConnection
            )

            # Modèle d'index ECS simplifié pour Suricata
            index_template_body = {
                "index_patterns": [index_pattern],
                "template": {
                    "settings": {
                        "number_of_shards": 1,
                        "number_of_replicas": 0 # Pour un POC, pas de réplicas
                    },
                    "mappings": {
                        "properties": {
                            "@timestamp": {"type": "date"},
                            "event": {"properties": {"kind": {"type": "keyword"}, "category": {"type": "keyword"}, "type": {"type": "keyword"}}},
                            "source": {"properties": {"ip": {"type": "ip"}}},
                            "destination": {"properties": {"ip": {"type": "ip"}}},
                            "suricata": {"properties": {"signature": {"type": "text"}, "severity": {"type": "integer"}}}
                            # Ajoutez d'autres champs ECS pertinents de Suricata
                        }
                    }
                }
            }

            logging.info(f"Application du modèle d'index '{template_name}' pour le pattern '{index_pattern}'...")
            response = client.indices.put_index_template(name=template_name, body=index_template_body)
            
            if response.get('acknowledged'):
                logging.info(f"Modèle d'index '{template_name}' appliqué avec succès.")
                return True
            else:
                logging.error(f"Échec de l'application du modèle d'index '{template_name}' : {json.dumps(response, indent=2)}")
                self.shared_state['last_error'] = f"OpenSearch index template failed: {json.dumps(response)}"
                return False

        except Exception as e:
            logging.error(f"Erreur lors de l'application du modèle d'index OpenSearch : {e}")
            self.shared_state['last_error'] = f"OpenSearch index template error: {e}"
            return False

# Exemple d'utilisation (pour les tests)
if __name__ == "__main__":
    import os
    from config_manager import ConfigManager
    import multiprocessing
    
    # Créer un fichier config.yaml temporaire pour le test
    temp_config_content = """
    aws:
      access_key_id: "YOUR_AWS_ACCESS_KEY_ID" # Remplacer par votre clé d'accès AWS
      secret_access_key: "YOUR_AWS_SECRET_ACCESS_KEY" # Remplacer par votre clé secrète AWS
      region: "eu-central-1"
      domain_name: "test-suricata-prod" # Utiliser un nom de domaine de test
      opensearch_endpoint: "" # Sera rempli par le manager
    """
    with open('temp_config.yaml', 'w') as f:
        f.write(temp_config_content)

    try:
        config_mgr = ConfigManager(config_path='temp_config.yaml')
        manager = multiprocessing.Manager()
        shared_state = manager.dict({
            'aws_ready': False,
            'last_error': ''
        })

        aws_mgr = AWSManager(config_mgr, shared_state)

        print("\nTest de provisioning du domaine OpenSearch...")
        # Le provisioning réel prend du temps, pour le test, nous allons simuler
        # ou nous assurer qu'un domaine de test existe déjà.
        # Pour un test unitaire, il est préférable de mocker les appels boto3.
        # Ici, nous allons appeler la fonction, mais elle échouera sans vrais identifiants/domaine.
        # success_provision = aws_mgr.provision_opensearch_domain()
        # print(f"Provisioning réussi : {success_provision}")
        # print(f"Endpoint OpenSearch : {config_mgr.get('aws.opensearch_endpoint')}")

        # Simuler un endpoint pour les tests d'envoi et de template
        config_mgr.config['aws']['opensearch_endpoint'] = "https://mock-opensearch-domain.eu-central-1.es.amazonaws.com"
        aws_mgr.opensearch_endpoint = config_mgr.get('aws.opensearch_endpoint')
        aws_mgr.session = boto3.Session(
            aws_access_key_id="MOCK_ACCESS_KEY",
            aws_secret_access_key="MOCK_SECRET_KEY",
            region_name="eu-central-1"
        )
        
        print("\nTest d'application du modèle d'index (simulé)...")
        # success_template = aws_mgr.apply_index_template()
        # print(f"Application du modèle réussie : {success_template}")

        sample_logs = [
            {"@timestamp": "2026-01-01T10:00:00Z", "event": {"action": "alert", "kind": "alert", "category": "network"}, "source": {"ip": "192.168.1.1"}, "destination": {"ip": "10.0.0.5"}, "suricata": {"signature": "ET SCAN", "severity": 2}},
            {"@timestamp": "2026-01-01T10:00:01Z", "event": {"action": "drop", "kind": "event", "category": "network"}, "source": {"ip": "10.0.0.5"}, "destination": {"ip": "192.168.1.1"}, "suricata": {"signature": "DROP", "severity": 1}}
        ]

        print("\nTest d'envoi de logs à OpenSearch (simulé)...")
        # Pour un test réel, il faudrait un serveur OpenSearch mocké ou réel.
        # success_send = aws_mgr.send_bulk_to_opensearch(sample_logs)
        # print(f"Envoi réussi : {success_send}")
        print(f"État partagé aws_ready : {shared_state['aws_ready']}")
        print(f"État partagé last_error : {shared_state['last_error']}")

    except Exception as e:
        logging.error(f"Erreur lors du test de AWSManager: {e}")
    finally:
        if os.path.exists('temp_config.yaml'):
            os.remove('temp_config.yaml')
