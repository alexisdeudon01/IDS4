"""
Tailscale network monitoring.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from ids.datastructures import TailscaleNode

logger = logging.getLogger(__name__)

TAILSCALE_AVAILABLE = False
TAILSCALE_SDK = None
PythonTailscale = None
try:
    from python_tailscale import Tailscale as PythonTailscale

    TAILSCALE_AVAILABLE = True
    TAILSCALE_SDK = "python-tailscale"
except ImportError:
    try:
        from tailscale import Tailscale

        TAILSCALE_AVAILABLE = True
        TAILSCALE_SDK = "tailscale"
    except ImportError:
        logger.warning("tailscale SDK not available. Install with: pip install python-tailscale")


class TailscaleMonitor:
    """Monitor Tailscale tailnet nodes."""

    def __init__(self, tailnet: str | None, api_key: str) -> None:
        """
        Initialize Tailscale monitor.

        Args:
            tailnet: Tailnet name (optional, will be auto-detected if None)
            api_key: Tailscale API key
        """
        self.api_key = api_key
        self.tailnet = tailnet
        self._client: Any = None

        if TAILSCALE_AVAILABLE and TAILSCALE_SDK == "python-tailscale":
            try:
                self._client = PythonTailscale(api_key=api_key, tailnet=tailnet)
                logger.info(f"Python-Tailscale monitor initialized for tailnet: {tailnet}")
            except Exception as e:
                logger.error(f"Failed to initialize python-tailscale client: {e}")
        elif TAILSCALE_AVAILABLE:
            try:
                # Si pas de tailnet, essayer de le détecter
                if not self.tailnet:
                    self.tailnet = self._detect_tailnet()
                
                if self.tailnet:
                    self._client = Tailscale(tailnet=self.tailnet, api_key=api_key)
                    logger.info(f"Tailscale monitor initialized for tailnet: {self.tailnet}")
                else:
                    logger.warning("Tailnet not found, Tailscale monitoring disabled")
            except Exception as e:
                logger.error(f"Failed to initialize Tailscale client: {e}")
        else:
            logger.warning("Tailscale SDK not available")
    
    def _detect_tailnet(self) -> str | None:
        """Détecte le tailnet depuis l'API key."""
        try:
            import json
            import urllib.request
            from urllib.parse import urlparse
            
            url = "https://api.tailscale.com/api/v2/user/self"
            parsed = urlparse(url)
            if parsed.scheme != "https":
                return None
            
            headers = {"Authorization": f"Bearer {self.api_key}"}
            req = urllib.request.Request(url, headers=headers, method="GET")
            # bandit: B310 - URL scheme validated above
            with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
                response = json.loads(resp.read().decode("utf-8"))
                tailnet = response.get("LoginName") or response.get("Profile", {}).get("LoginName")
                if tailnet and "@" in tailnet:
                    return tailnet.split("@")[1]
                return tailnet
        except Exception as e:
            logger.warning(f"Could not auto-detect tailnet: {e}")
        return None

    async def get_nodes(self) -> list[TailscaleNode]:
        """
        Get list of authorized nodes in the tailnet.

        Returns:
            List of TailscaleNode objects
        """
        if not self._client:
            return []

        try:
            devices = await self._client.devices()
            nodes: list[TailscaleNode] = []

            device_entries = devices.devices.values() if hasattr(devices, "devices") else devices
            for device in device_entries:
                if not device.authorized:
                    continue

                # Get last seen time
                last_seen: datetime | None = None
                if hasattr(device, "last_seen") and device.last_seen:
                    last_seen = datetime.fromisoformat(str(device.last_seen).replace("Z", "+00:00"))

                # Get primary IP
                ip = ""
                if device.addresses:
                    ip = device.addresses[0]

                node = TailscaleNode(
                    name=device.name or "unknown",
                    ip=ip,
                    online=device.online if hasattr(device, "online") else False,
                    last_seen=last_seen,
                    tags=list(device.tags) if hasattr(device, "tags") else [],
                )
                nodes.append(node)

            return nodes

        except Exception as e:
            logger.error(f"Error getting Tailscale nodes: {e}")
            return []
