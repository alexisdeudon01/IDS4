"""
Charge les secrets depuis secret.json et les expose comme variables d'environnement.
"""

from __future__ import annotations

import json
import os
from pathlib import Path


def load_secrets_from_json(secret_path: Path | None = None) -> dict:
    """
    Charge les secrets depuis secret.json.

    Args:
        secret_path: Chemin vers secret.json (défaut: secret.json à la racine)

    Returns:
        Dictionnaire des secrets
    """
    if secret_path is None:
        # Chercher secret.json à la racine du projet
        repo_root = Path(__file__).parent.parent.parent.parent
        secret_path = repo_root / "secret.json"

    if not secret_path.exists():
        return {}

    try:
        with secret_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def set_env_from_secrets(secret_path: Path | None = None) -> None:
    """
    Charge les secrets depuis secret.json et les définit comme variables d'environnement.

    Args:
        secret_path: Chemin vers secret.json
    """
    secrets = load_secrets_from_json(secret_path)

    # AWS
    aws = secrets.get("aws", {})
    if aws.get("access_key_id") and not os.getenv("AWS_ACCESS_KEY_ID"):
        os.environ["AWS_ACCESS_KEY_ID"] = aws["access_key_id"]
    if aws.get("secret_access_key") and not os.getenv("AWS_SECRET_ACCESS_KEY"):
        os.environ["AWS_SECRET_ACCESS_KEY"] = aws["secret_access_key"]
    if aws.get("session_token") and not os.getenv("AWS_SESSION_TOKEN"):
        os.environ["AWS_SESSION_TOKEN"] = aws["session_token"]

    # Tailscale
    tailscale = secrets.get("tailscale", {})
    if tailscale.get("tailnet") and not os.getenv("TAILSCALE_TAILNET"):
        os.environ["TAILSCALE_TAILNET"] = tailscale["tailnet"]
    if tailscale.get("api_key") and not os.getenv("TAILSCALE_API_KEY"):
        os.environ["TAILSCALE_API_KEY"] = tailscale["api_key"]
    if tailscale.get("oauth_client_id") and not os.getenv("TAILSCALE_OAUTH_CLIENT_ID"):
        os.environ["TAILSCALE_OAUTH_CLIENT_ID"] = tailscale["oauth_client_id"]
    if tailscale.get("oauth_client_secret") and not os.getenv("TAILSCALE_OAUTH_CLIENT_SECRET"):
        os.environ["TAILSCALE_OAUTH_CLIENT_SECRET"] = tailscale["oauth_client_secret"]

    # Elasticsearch
    elasticsearch = secrets.get("elasticsearch", {})
    if elasticsearch.get("username") and not os.getenv("ELASTICSEARCH_USERNAME"):
        os.environ["ELASTICSEARCH_USERNAME"] = elasticsearch["username"]
    if elasticsearch.get("password") and not os.getenv("ELASTICSEARCH_PASSWORD"):
        os.environ["ELASTICSEARCH_PASSWORD"] = elasticsearch["password"]

    # Anthropic (optionnel - AI Healing, non utilisé dans les scripts de déploiement)
    anthropic = secrets.get("anthropic", {})
    if anthropic.get("api_key") and not os.getenv("ANTHROPIC_API_KEY"):
        os.environ["ANTHROPIC_API_KEY"] = anthropic["api_key"]
    
    # Dashboard config (valeurs par défaut, optionnel)
    dashboard = secrets.get("dashboard", {})
    if dashboard.get("port") and not os.getenv("DASHBOARD_PORT"):
        os.environ["DASHBOARD_PORT"] = str(dashboard["port"])
    if dashboard.get("mirror_interface") and not os.getenv("MIRROR_INTERFACE"):
        os.environ["MIRROR_INTERFACE"] = dashboard["mirror_interface"]
    if dashboard.get("led_pin") and not os.getenv("LED_PIN"):
        os.environ["LED_PIN"] = str(dashboard["led_pin"])


# Charger automatiquement au démarrage
set_env_from_secrets()
