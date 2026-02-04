"""
Network interface monitoring (eth0 traffic from port mirroring).
"""

from __future__ import annotations

import asyncio
import logging
import subprocess
from datetime import datetime
from typing import Any

import psutil

from ids.datastructures import NetworkStats

logger = logging.getLogger(__name__)


class NetworkMonitor:
    """Monitor network interface statistics (eth0 for mirrored traffic)."""

    def __init__(self, interface: str = "eth0") -> None:
        """
        Initialize network monitor.

        Args:
            interface: Network interface to monitor (default: eth0)
        """
        self.interface = interface
        self._last_stats: dict[str, int] | None = None
        self._last_timestamp: float | None = None

    async def get_interface_stats(self) -> NetworkStats | None:
        """
        Get current network interface statistics.

        Returns:
            NetworkStats object or None if interface not found
        """
        try:
            net_io = psutil.net_io_counters(pernic=True)
            if self.interface not in net_io:
                logger.warning(f"Interface {self.interface} not found")
                return None

            stats = net_io[self.interface]
            now = datetime.now()
            current_timestamp = now.timestamp()

            # Calculate bitrate if we have previous stats
            bitrate_sent = 0.0
            bitrate_recv = 0.0

            if self._last_stats and self._last_timestamp:
                time_delta = current_timestamp - self._last_timestamp
                if time_delta > 0:
                    bytes_sent_delta = stats.bytes_sent - self._last_stats.get("bytes_sent", 0)
                    bytes_recv_delta = stats.bytes_recv - self._last_stats.get("bytes_recv", 0)

                    bitrate_sent = (bytes_sent_delta * 8) / time_delta  # bits per second
                    bitrate_recv = (bytes_recv_delta * 8) / time_delta  # bits per second

            # Update last stats
            self._last_stats = {
                "bytes_sent": stats.bytes_sent,
                "bytes_recv": stats.bytes_recv,
            }
            self._last_timestamp = current_timestamp

            return NetworkStats(
                interface=self.interface,
                bytes_sent=stats.bytes_sent,
                bytes_recv=stats.bytes_recv,
                packets_sent=stats.packets_sent,
                packets_recv=stats.packets_recv,
                errin=stats.errin,
                errout=stats.errout,
                dropin=stats.dropin,
                dropout=stats.dropout,
                bitrate_sent=bitrate_sent,
                bitrate_recv=bitrate_recv,
                timestamp=now,
            )

        except Exception as e:
            logger.error(f"Error getting interface stats: {e}")
            return None

    async def ensure_promiscuous_mode(self) -> bool:
        """
        Ensure the interface is in promiscuous mode for port mirroring.

        Returns:
            True if promiscuous mode is enabled
        """
        try:
            # Check current mode
            result = subprocess.run(
                ["ip", "link", "show", self.interface],
                capture_output=True,
                text=True,
                check=False,
            )

            if "PROMISC" in result.stdout:
                logger.debug(f"Interface {self.interface} already in promiscuous mode")
                return True

            # Enable promiscuous mode
            result = subprocess.run(
                ["sudo", "ip", "link", "set", self.interface, "promisc", "on"],
                capture_output=True,
                text=True,
                check=True,
            )

            logger.info(f"Enabled promiscuous mode on {self.interface}")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to enable promiscuous mode: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Error setting promiscuous mode: {e}")
            return False

    async def verify_span_config(self, switch_ip: str, switch_user: str, switch_password: str) -> dict[str, Any]:
        """
        Verify SPAN/Port Mirroring configuration on switch using Netmiko.

        Args:
            switch_ip: Switch IP address
            switch_user: Switch username
            switch_password: Switch password

        Returns:
            Dictionary with verification results
        """
        try:
            from netmiko import ConnectHandler

            device = {
                "device_type": "generic",
                "host": switch_ip,
                "username": switch_user,
                "password": switch_password,
            }

            # Note: TP-Link TL-SG108E doesn't support SSH/CLI
            # This is a placeholder for switches that do support it
            # For TL-SG108E, use the httpx-based web interface method instead

            logger.warning(
                "Netmiko SPAN verification not supported for TP-Link TL-SG108E. "
                "Use web interface automation instead."
            )

            return {
                "verified": False,
                "method": "netmiko",
                "note": "TP-Link TL-SG108E requires web interface automation",
            }

        except ImportError:
            logger.warning("netmiko not available")
            return {
                "verified": False,
                "error": "netmiko not installed",
            }
        except Exception as e:
            logger.error(f"Error verifying SPAN config: {e}")
            return {
                "verified": False,
                "error": str(e),
            }
