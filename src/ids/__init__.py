"""
IDS (Intrusion Detection System) - Système de détection d'intrusions avancé.

Package racine du système IDS avec architecture SOLID et injection de dépendances.
"""

__version__ = "2.0.0"
__author__ = "SIXT R&D"
__license__ = "MIT"

# Lazy imports to avoid circular dependencies
def __getattr__(name):
    if name == "AlerteIDS":
        from .domain import AlerteIDS
        return AlerteIDS
    elif name == "SeveriteAlerte":
        from .domain import SeveriteAlerte
        return SeveriteAlerte
    elif name == "TypeAlerte":
        from .domain import TypeAlerte
        return TypeAlerte
    elif name == "ConteneurDI":
        from .app.container import ConteneurDI
        return ConteneurDI
    raise AttributeError(f"module 'ids' has no attribute '{name}'")

__all__ = [
    "AlerteIDS",
    "SeveriteAlerte",
    "TypeAlerte",
    "ConteneurDI",
]
