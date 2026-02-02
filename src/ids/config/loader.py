"""
Gestionnaire de Configuration - Chargement et validation de config.yaml.

Implémente l'interface GestionnaireConfig de manière robuste.
"""

import yaml
import logging
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigManager:
    """
    Gère le chargement et l'accès à la configuration YAML.
    
    Implémente le Protocol GestionnaireConfig.
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialise le gestionnaire de configuration.
        
        Args:
            config_path: Chemin vers le fichier config.yaml
            
        Raises:
            FileNotFoundError: Si le fichier config n'existe pas
        """
        self.config_path = Path(config_path)
        self.logger = logging.getLogger(__name__)
        
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Fichier de configuration introuvable: {self.config_path}"
            )
        
        self._config = self._charger_config()
        self.logger.info(f"Configuration chargée depuis {self.config_path}")
    
    def _charger_config(self) -> Dict[str, Any]:
        """Charge le fichier YAML."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            self.logger.error(f"Erreur lors du parsing YAML: {e}")
            raise
    
    def obtenir(self, clé: str, defaut: Any = None) -> Any:
        """
        Obtient une valeur de configuration.
        
        Supporte les clés imbriquées avec notée pointée :
        Ex: "suricata.config_path" -> self._config["suricata"]["config_path"]
        
        Args:
            clé: Clé de configuration (peut contenir des points)
            defaut: Valeur par défaut si la clé n'existe pas
            
        Returns:
            La valeur de configuration ou la valeur par défaut
        """
        parties = clé.split('.')
        valeur = self._config
        
        for partie in parties:
            if isinstance(valeur, dict) and partie in valeur:
                valeur = valeur[partie]
            else:
                return defaut
        
        return valeur
    
    def get(self, clé: str, defaut: Any = None) -> Any:
        """Alias pour obtenir() pour la rétrocompatibilité."""
        return self.obtenir(clé, defaut)
    
    def definir(self, clé: str, valeur: Any) -> None:
        """
        Définit une valeur de configuration.
        
        Warning: Cela modifie la configuration en mémoire uniquement,
        pas le fichier sur disque.
        
        Args:
            clé: Clé de configuration
            valeur: Valeur à définir
        """
        parties = clé.split('.')
        config = self._config
        
        for partie in parties[:-1]:
            if partie not in config:
                config[partie] = {}
            config = config[partie]
        
        config[parties[-1]] = valeur
        self.logger.debug(f"Configuration modifiée: {clé} = {valeur}")
    
    def recharger(self) -> None:
        """Recharge la configuration depuis le fichier."""
        self._config = self._charger_config()
        self.logger.info("Configuration rechargée")
    
    def get_all(self) -> Dict[str, Any]:
        """Retourne la configuration complète."""
        return self._config.copy()
    
    def __repr__(self) -> str:
        return f"ConfigManager({self.config_path})"


__all__ = ["ConfigManager"]
