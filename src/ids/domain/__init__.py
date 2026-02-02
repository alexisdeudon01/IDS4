"""
Domain - Entités de données structurées (Data-Oriented Design).

Définit les modèles de données immuables qui représentent le domaine métier.
Utilise dataclasses pour la clarté et la performance.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional
from uuid import uuid4, UUID


class SeveriteAlerte(Enum):
    """Niveaux de sévérité des alertes."""
    CRITIQUE = "critique"
    HAUTE = "haute"
    MOYENNE = "moyenne"
    BASSE = "basse"


class TypeAlerte(Enum):
    """Types d'alertes générées par le système."""
    INTRUSION = "intrusion"
    ANOMALIE = "anomalie"
    CONFORMITE = "conformite"
    RESSOURCE = "ressource"


@dataclass(frozen=True)
class AlerteIDS:
    """
    Entité immuable représentant une alerte de sécurité IDS.
    
    Propriétés :
        - Immutable (frozen=True) pour garantir l'intégrité
        - Hashable pour utilisation dans sets/dicts
        - Serializable (compatible JSON via dataclasses-json)
    """
    id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    severite: SeveriteAlerte = SeveriteAlerte.MOYENNE
    type_alerte: TypeAlerte = TypeAlerte.INTRUSION
    source_ip: str = ""
    destination_ip: str = ""
    port: int = 0
    protocole: str = "TCP"
    signature: str = ""
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __hash__(self):
        """Permet l'utilisation dans des sets et comme clés dict."""
        return hash((self.id, self.timestamp, self.source_ip))
    
    def __repr__(self) -> str:
        return (
            f"AlerteIDS(id={self.id.hex[:8]}, "
            f"severite={self.severite.value}, "
            f"{self.source_ip}->{self.destination_ip}:{self.port})"
        )


@dataclass(frozen=True)
class ConfigurationIDS:
    """
    Configuration système immuable.
    
    Représente l'état de configuration du système à un moment donné.
    """
    version: str = "2.0.0"
    interface_reseau: str = "eth0"
    repertoire_logs: str = "/mnt/ram_logs"
    repertoire_config: str = "config/"
    
    # Suricata
    suricata_config_path: str = "suricata/suricata.yaml"
    suricata_rules_path: str = "suricata/rules/"
    suricata_eve_log: str = "/mnt/ram_logs/eve.json"
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    # AWS OpenSearch
    aws_region: str = "eu-west-1"
    aws_opensearch_domain: str = "ids-opensearch"
    aws_opensearch_endpoint: Optional[str] = None
    
    # Docker
    docker_compose_path: str = "docker/docker-compose.yml"
    
    # Ressources
    cpu_limit_percent: float = 80.0
    ram_limit_percent: float = 85.0
    throttling_enabled: bool = True
    
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MetriquesSystem:
    """Métriques système actuelles."""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    cpu_usage: float = 0.0
    ram_usage: float = 0.0
    alertes_par_seconde: float = 0.0
    alertes_en_queue: int = 0
    uptime_secondes: int = 0
    erreurs_recentes: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ConditionSante:
    """État de santé d'un composant."""
    nom_composant: str
    sain: bool
    message: str = ""
    derniere_verification: datetime = field(default_factory=datetime.utcnow)
    details: Dict[str, Any] = field(default_factory=dict)


__all__ = [
    "SeveriteAlerte",
    "TypeAlerte",
    "AlerteIDS",
    "ConfigurationIDS",
    "MetriquesSystem",
    "ConditionSante",
]
