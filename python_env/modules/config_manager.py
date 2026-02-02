import yaml
import os

class ConfigManager:
    """
    Gère le chargement et l'accès aux paramètres de configuration du projet.
    """
    def __init__(self, config_path='config.yaml'):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self):
        """
        Charge le fichier de configuration YAML.
        """
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Le fichier de configuration n'a pas été trouvé à : {self.config_path}")
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)

    def get(self, key, default=None):
        """
        Récupère une valeur de configuration par sa clé.
        Supporte les clés imbriquées (ex: 'raspberry_pi.cpu_limit_percent').
        """
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def reload_config(self):
        """
        Recharge le fichier de configuration.
        """
        self.config = self._load_config()
        print("Configuration rechargée.")

# Exemple d'utilisation (pour les tests ou le développement)
if __name__ == "__main__":
    # Créer un fichier config.yaml temporaire pour le test
    temp_config_content = """
    test_section:
      key1: "value1"
      key2: 123
    another_key: true
    """
    with open('temp_config.yaml', 'w') as f:
        f.write(temp_config_content)

    try:
        config_mgr = ConfigManager(config_path='temp_config.yaml')
        print(f"Valeur de test_section.key1 : {config_mgr.get('test_section.key1')}")
        print(f"Valeur de test_section.key2 : {config_mgr.get('test_section.key2')}")
        print(f"Valeur de another_key : {config_mgr.get('another_key')}")
        print(f"Valeur d'une clé inexistante : {config_mgr.get('non_existent_key', 'default_value')}")

        # Tester le rechargement
        print("\nModification du fichier de configuration temporaire...")
        with open('temp_config.yaml', 'w') as f:
            f.write("new_key: 'new_value'\n")
        config_mgr.reload_config()
        print(f"Nouvelle valeur de new_key : {config_mgr.get('new_key')}")

    except FileNotFoundError as e:
        print(f"Erreur : {e}")
    finally:
        # Nettoyer le fichier temporaire
        if os.path.exists('temp_config.yaml'):
            os.remove('temp_config.yaml')
