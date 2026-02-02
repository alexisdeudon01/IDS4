"""
Injection de Dépendances - Conteneur DI avec punq.

Gère l'enregistrement et la résolution de tous les services du système.
Suit le pattern Inversion of Control (IoC).
"""

from typing import Dict, Any, Type, TypeVar, Optional, Callable
import logging
from functools import lru_cache

try:
    import punq
except ImportError:
    raise ImportError(
        "punq n'est pas installé. "
        "Installez-le avec: pip install punq"
    )

from ..domain import ConfigurationIDS
from ..interfaces import (
    AlerteSource,
    GestionnaireComposant,
    GestionnaireConfig,
)
from ..config.loader import ConfigManager

T = TypeVar("T")

logger = logging.getLogger(__name__)


class ConteneurDI:
    """
    Conteneur d'injection de dépendances.
    
    Enregistre et résout les services du système selon les principes SOLID.
    Exemple d'utilisation :
    
        container = ConteneurDI()
        container.enregistrer_services(config)
        
        # Résoudre un service
        suricata_mgr = container.resoudre(AlerteSource)
        resource_ctrl = container.resoudre(ResourceController)
    """
    
    def __init__(self):
        """Initialise le conteneur."""
        self._container = punq.Container()
        self._instances: Dict[Type, Any] = {}
        self._logger = logging.getLogger(__name__)
    
    def enregistrer_singleton(
        self,
        interface: Type[T],
        instance: T,
    ) -> None:
        """
        Enregistre une instance singleton.
        
        Args:
            interface: Le type/interface du service
            instance: L'instance à enregistrer
        """
        self._container.register(interface, instance=instance)
        self._instances[interface] = instance
        self._logger.debug(f"Singleton enregistré: {interface.__name__}")
    
    def enregistrer_factory(
        self,
        interface: Type[T],
        factory: Callable[..., T],
    ) -> None:
        """
        Enregistre une factory pour créer des instances.
        
        Args:
            interface: Le type/interface du service
            factory: Une fonction qui crée l'instance
        """
        self._container.register(interface, factory=factory)
        self._logger.debug(f"Factory enregistrée: {interface.__name__}")
    
    def enregistrer_classe(
        self,
        interface: Type[T],
        impl: Type[T],
    ) -> None:
        """
        Enregistre une classe d'implémentation pour une interface.
        
        Args:
            interface: L'interface (Protocol)
            impl: L'implémentation concrète
        """
        self._container.register(interface, factory=impl)
        self._logger.debug(
            f"Classe enregistrée: {interface.__name__} -> {impl.__name__}"
        )
    
    def enregistrer_services(self, config_dict: Dict[str, Any]) -> None:
        """
        Enregistre tous les services du système.
        
        À appeler une seule fois au démarrage de l'application.
        
        Args:
            config_dict: Dictionnaire de configuration
        """
        self._logger.info("Enregistrement des services...")
        
        # 1. Enregistrer ConfigurationIDS
        config = ConfigurationIDS(**{
            k: v for k, v in config_dict.items()
            if k in ConfigurationIDS.__dataclass_fields__
        })
        self.enregistrer_singleton(ConfigurationIDS, config)
        
        # 2. Enregistrer ConfigManager
        config_mgr = ConfigManager(config_dict)
        self.enregistrer_singleton(GestionnaireConfig, config_mgr)
        
        # 3. Enregistrer AlerteSource (implémentation: SuricataManager)
        # À adapter selon votre implémentation réelle
        # self.enregistrer_factory(AlerteSource, lambda: SuricataManager(...))
        
        # 4. Enregistrer les composants
        # À compléter selon vos composants réels
        # self.enregistrer_classe(ResourceController, ResourceController)
        # self.enregistrer_classe(DockerManager, DockerManager)
        
        self._logger.info("Services enregistrés avec succès")
    
    def resoudre(self, service_type: Type[T]) -> T:
        """
        Résout et instancie un service.
        
        Args:
            service_type: Le type du service à résoudre
            
        Returns:
            L'instance du service
            
        Raises:
            punq.MissingDependencyError: Si le service n'est pas enregistré
        """
        # Retourner le singleton si déjà créé
        if service_type in self._instances:
            return self._instances[service_type]
        
        # Sinon, le conteneur le crée
        instance = self._container.resolve(service_type)
        self._logger.debug(f"Service résolu: {service_type.__name__}")
        return instance
    
    @lru_cache(maxsize=128)
    def resoudre_en_cache(self, service_type: Type[T]) -> T:
        """Résout un service avec cache LRU."""
        return self.resoudre(service_type)
    
    def enregistrer_plusieurs(
        self,
        mapping: Dict[Type, Type],
    ) -> None:
        """
        Enregistre plusieurs mappages interface->implémentation.
        
        Args:
            mapping: Dict {Interface: Implémentation}
        """
        for interface, impl in mapping.items():
            self.enregistrer_classe(interface, impl)
    
    def enregistrer_factories(
        self,
        factories: Dict[Type, Callable],
    ) -> None:
        """
        Enregistre plusieurs factories.
        
        Args:
            factories: Dict {Interface: factory_function}
        """
        for interface, factory in factories.items():
            self.enregistrer_factory(interface, factory)


class ConteneurFactory:
    """Factory pour créer et configurer un conteneur DI."""
    
    @staticmethod
    def creer_conteneur_test() -> ConteneurDI:
        """Crée un conteneur pour les tests."""
        container = ConteneurDI()
        # Enregistrer des mocks/fakes pour les tests
        # À adapter selon vos tests
        return container
    
    @staticmethod
    def creer_conteneur_prod(config_path: str) -> ConteneurDI:
        """
        Crée un conteneur pour la production.
        
        Args:
            config_path: Chemin vers le fichier de configuration
        """
        config_mgr = ConfigManager(config_path)
        config_dict = config_mgr.get_all()
        
        container = ConteneurDI()
        container.enregistrer_services(config_dict)
        return container


__all__ = [
    "ConteneurDI",
    "ConteneurFactory",
]
