#!/usr/bin/env python3
"""
Main launcher for IDS Dashboard.

Ensures FastAPI backend is running and serves the dashboard.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import uvicorn

# Charger les secrets depuis secret.json avant d'importer l'app
from .load_secrets import set_env_from_secrets

# Charger les secrets
set_env_from_secrets()

from .app import create_dashboard_app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def main() -> None:
    """Launch the IDS Dashboard."""
    import os

    app = create_dashboard_app()

    host = "0.0.0.0"
    port = int(os.getenv("DASHBOARD_PORT", "8080"))

    logger.info(f"Starting IDS Dashboard on {host}:{port}")

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True,
    )


if __name__ == "__main__":
    import os

    main()
