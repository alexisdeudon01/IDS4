import psutil
import time
import multiprocessing
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(processName)s - %(levelname)s - %(message)s')

class ResourceController:
    """
    Contrôle et régule l'utilisation des ressources CPU et RAM.
    """
    def __init__(self, shared_state, config_manager):
        self.shared_state = shared_state
        self.config = config_manager
        self.cpu_limit = self.config.get('raspberry_pi.cpu_limit_percent', 70)
        self.ram_limit = self.config.get('raspberry_pi.ram_limit_percent', 70)
        self.sleep_interval = 1 # Intervalle de surveillance initial en secondes
        self.throttling_level = multiprocessing.Value('i', 0) # 0: normal, 1: léger, 2: modéré, 3: sévère

    def _get_system_metrics(self):
        """
        Récupère l'utilisation actuelle du CPU et de la RAM.
        """
        cpu_percent = psutil.cpu_percent(interval=None) # Non-bloquant
        ram_percent = psutil.virtual_memory().percent
        return cpu_percent, ram_percent

    def _apply_throttling(self, cpu_usage, ram_usage):
        """
        Applique une stratégie de régulation basée sur l'utilisation des ressources.
        Met à jour le niveau de régulation dans l'état partagé.
        """
        current_throttling_level = 0
        if cpu_usage > self.cpu_limit or ram_usage > self.ram_limit:
            if cpu_usage > (self.cpu_limit + 10) or ram_usage > (self.ram_limit + 10):
                current_throttling_level = 3 # Sévère
            elif cpu_usage > (self.cpu_limit + 5) or ram_usage > (self.ram_limit + 5):
                current_throttling_level = 2 # Modéré
            else:
                current_throttling_level = 1 # Léger
        
        with self.throttling_level.get_lock():
            self.throttling_level.value = current_throttling_level
        
        self.shared_state['throttling_level'] = current_throttling_level

        if current_throttling_level > 0:
            logging.warning(f"Régulation activée : niveau {current_throttling_level}. CPU: {cpu_usage:.2f}%, RAM: {ram_usage:.2f}%")
            # Ajuster les intervalles de sommeil pour les processus consommateurs
            # Cette logique sera implémentée dans les processus enfants qui liront throttling_level
        else:
            logging.info(f"Régulation désactivée. CPU: {cpu_usage:.2f}%, RAM: {ram_usage:.2f}%")

    def run(self):
        """
        Boucle principale du contrôleur de ressources.
        """
        logging.info("Processus de Contrôle / Ressources démarré.")
        while True:
            cpu_usage, ram_usage = self._get_system_metrics()

            self.shared_state['cpu_usage'] = cpu_usage
            self.shared_state['ram_usage'] = ram_usage

            self._apply_throttling(cpu_usage, ram_usage)

            # Ajuster l'intervalle de surveillance si nécessaire, mais rester réactif
            time.sleep(self.sleep_interval)

# Exemple d'utilisation (pour les tests)
if __name__ == "__main__":
    import os # Ajout de l'import os
    from config_manager import ConfigManager
    
    # Créer un fichier config.yaml temporaire pour le test
    temp_config_content = """
    raspberry_pi:
      cpu_limit_percent: 70
      ram_limit_percent: 70
    """
    with open('temp_config.yaml', 'w') as f:
        f.write(temp_config_content)

    try:
        config_mgr = ConfigManager(config_path='temp_config.yaml')
        manager = multiprocessing.Manager()
        shared_state = manager.dict({
            'cpu_usage': 0.0,
            'ram_usage': 0.0,
            'throttling_level': 0
        })

        controller = ResourceController(shared_state, config_mgr)
        
        # Simuler une exécution pendant quelques secondes
        process = multiprocessing.Process(target=controller.run, name="ResourceControllerProcess")
        process.start()
        
        for _ in range(10):
            time.sleep(2)
            # Accès direct car les mises à jour sont atomiques pour les types simples
            print(f"État partagé - CPU: {shared_state['cpu_usage']:.2f}%, RAM: {shared_state['ram_usage']:.2f}%, Throttling: {shared_state['throttling_level']}")
        
        process.terminate()
        process.join()

    except Exception as e:
        logging.error(f"Erreur lors du test du ResourceController: {e}")
    finally:
        if os.path.exists('temp_config.yaml'):
            os.remove('temp_config.yaml')
