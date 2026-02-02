"""
Package fixtures - Fixtures réutilisables pour pytest.
"""

from .alerte_fixtures import (
    alerte_ids_simple,
    alerte_ids_critique,
    alerte_ids_batch,
    alerte_ids_tous_types,
    alerte_factory,
)

from .config_fixtures import (
    config_dict_test,
    config_ids_test,
    config_manager_test,
    config_minimal,
    config_factory,
)

from .container_fixtures import (
    container_di_test,
    container_factory,
)

__all__ = [
    # Alerte fixtures
    "alerte_ids_simple",
    "alerte_ids_critique",
    "alerte_ids_batch",
    "alerte_ids_tous_types",
    "alerte_factory",
    
    # Config fixtures
    "config_dict_test",
    "config_ids_test",
    "config_manager_test",
    "config_minimal",
    "config_factory",
    
    # Container fixtures
    "container_di_test",
    "container_factory",
]
