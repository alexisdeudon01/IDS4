"""
Interfaces (Protocol) - Contrats sans implémentation (DIP - Dependency Inversion).

Utilise le type hinting Protocol de typing pour définir des interfaces.
Cela permet une dépendance vers les abstractions plutôt que les implémentations concrètes.
"""

from typing import Protocol, AsyncGenerator, Optional, Dict, Any
from datetime import datetime
from ..domain import AlerteIDS, ConditionSante


class AlerteSource(Protocol):
    """
    Interface pour une source d'alertes IDS.
    
    Implémentée par SuricataManager, mais peut être remplacée par
    une autre source (fichier, API, etc.) sans modifier le code client.
    """
    
    async def fournir_alertes(self) -> AsyncGenerator[AlerteIDS, None]:
        """
        Fournit un flux continu d'alertes.
        
        Yields:
            AlerteIDS: Les alertes générées par la source
            
        Raises:
            AlerteSourceIndisponible: Si la source devient indisponible
        """
        ...
    
    async def valider_connexion(self) -> bool:
        """
        Valide la connexion à la source d'alertes.
        
        Returns:
            bool: True si la source est opérationnelle, False sinon
        """
        ...
    
    async def arreter(self) -> None:
        """Arrête proprement la source d'alertes."""
        ...


class GestionnaireComposant(Protocol):
    """
    Interface pour les composants gérés (managers).
    
    Tous les composants (Suricata, Docker, Metrics, etc.) implémentent
    ce contrat pour un cycle de vie uniforme.
    """
    
    async def demarrer(self) -> None:
        """
        Démarre le composant.
        
        Raises:
            ErreurIDS: Si le démarrage échoue
        """
        ...
    
    async def arreter(self) -> None:
        """Arrête proprement le composant."""
        ...
    
    async def verifier_sante(self) -> ConditionSante:
        """
        Vérifie l'état de santé du composant.
        
        Returns:
            ConditionSante: État actuel du composant
        """
        ...
    
    async def recharger_config(self) -> None:
        """Recharge la configuration du composant."""
        ...


class GestionnaireConfig(Protocol):
    """Interface pour la gestion de configuration."""
    
    def obtenir(self, clé: str, defaut: Any = None) -> Any:
        """Obtient une valeur de configuration."""
        ...
    
    def definir(self, clé: str, valeur: Any) -> None:
        """Définit une valeur de configuration."""
        ...
    
    def recharger(self) -> None:
        """Recharge la configuration depuis la source."""
        ...


class PersistanceAlertes(Protocol):
    """Interface pour la persistance d'alertes."""
    
    async def sauvegarder(self, alerte: AlerteIDS) -> None:
        """Sauvegarde une alerte."""
        ...
    
    async def recuperer(self, id_alerte: str) -> Optional[AlerteIDS]:
        """Récupère une alerte par son ID."""
        ...
    
    async def lister_recentes(self, nb: int = 100) -> list[AlerteIDS]:
        """Liste les alertes récentes."""
        ...


class LoggerIDS(Protocol):
    """Interface pour la journalisation."""
    
    def info(self, message: str) -> None:
        """Loggue une information."""
        ...
    
    def erreur(self, message: str, exception: Optional[Exception] = None) -> None:
        """Loggue une erreur."""
        ...
    
    def debug(self, message: str) -> None:
        """Loggue un message de debug."""
        ...


class MetriquesProvider(Protocol):
    """Interface pour la fourniture de métriques."""
    
    async def collecter_metriques(self) -> Dict[str, Any]:
        """Collecte les métriques actuelles du système."""
        ...
    
    async def enregistrer(self, nom: str, valeur: float) -> None:
        """Enregistre une métrique."""
        ...


__all__ = [
    "AlerteSource",
    "GestionnaireComposant",
    "GestionnaireConfig",
    "PersistanceAlertes",
    "LoggerIDS",
    "MetriquesProvider",
]
