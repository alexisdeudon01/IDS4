"""
IDS (Intrusion Detection System) - Système de détection d'intrusions avancé.

Package racine du système IDS avec architecture SOLID et injection de dépendances.
"""

__version__ = "2.0.0"
__author__ = "SIXT R&D"
__license__ = "MIT"

from .domain import AlerteIDS, SeveriteAlerte, TypeAlerte
from .interfaces import AlerteSource, GestionnaireComposant, GestionnaireConfig
from .app import ConteneurDI, AgentSupervisor

__all__ = [
    "AlerteIDS",
    "SeveriteAlerte",
    "TypeAlerte",
    "AlerteSource",
    "GestionnaireComposant",
    "GestionnaireConfig",
    "ConteneurDI",
    "AgentSupervisor",
]
