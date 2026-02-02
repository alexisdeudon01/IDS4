from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional

@dataclass
class AlerteIDS:
    """Modèle de données pour une alerte IDS."""
    signature_id: int
    signature: str
    timestamp: datetime = field(default_factory=datetime.now)
    severity: str = "medium"
    protocol: Optional[str] = None
    src_ip: Optional[str] = None
    src_port: Optional[int] = None
    dest_ip: Optional[str] = None
    dest_port: Optional[int] = None
    payload: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ConditionSante:
    """Modèle de données pour l'état de santé d'un composant."""
    nom_composant: str
    est_sain: bool
    message: str = "Opérationnel"
    derniere_verification: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)
