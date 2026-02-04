"""
Suricata EVE log monitoring with async tailing.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import AsyncIterator

from .models import AlertEvent

logger = logging.getLogger(__name__)

SURICATA_EVE_LOG = Path("/var/log/suricata/eve.json")


class SuricataLogMonitor:
    """Monitor Suricata EVE JSON log file for alert events."""

    def __init__(self, log_path: Path = SURICATA_EVE_LOG) -> None:
        """Initialize the monitor."""
        self.log_path = log_path
        self._running = False
        self._task: asyncio.Task | None = None
        self._position = 0

    async def start(self) -> None:
        """Start monitoring the log file."""
        if self._running:
            logger.warning("Suricata monitor already running")
            return

        if not self.log_path.exists():
            logger.warning(f"Suricata log file not found: {self.log_path}")
            return

        self._running = True
        # Get current file size to start from end
        if self.log_path.exists():
            self._position = self.log_path.stat().st_size

        logger.info(f"Started Suricata log monitoring: {self.log_path}")

    async def stop(self) -> None:
        """Stop monitoring."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped Suricata log monitoring")

    async def tail_alerts(self) -> AsyncIterator[AlertEvent]:
        """
        Async generator that yields alert events from the EVE log.

        Yields:
            AlertEvent objects for each 'alert' event type found
        """
        if not self.log_path.exists():
            logger.error(f"Log file does not exist: {self.log_path}")
            return

        while self._running:
            try:
                # Read new lines from current position
                with self.log_path.open(encoding="utf-8") as f:
                    f.seek(self._position)
                    new_lines = f.readlines()

                    for line in new_lines:
                        if not line.strip():
                            continue

                        try:
                            event = json.loads(line)
                            event_type = event.get("event_type", "")

                            # Only process alert events
                            if event_type == "alert":
                                alert_data = event.get("alert", {})
                                alert_event = AlertEvent(
                                    timestamp=datetime.fromisoformat(
                                        event.get("timestamp", "").replace("Z", "+00:00")
                                    ),
                                    event_type=event_type,
                                    src_ip=event.get("src_ip"),
                                    dest_ip=event.get("dest_ip"),
                                    alert=alert_data,
                                    severity=alert_data.get("severity", 0),
                                    signature=alert_data.get("signature", ""),
                                )
                                yield alert_event

                                # Update position after successful read
                                self._position = f.tell()

                        except json.JSONDecodeError as e:
                            logger.debug(f"Failed to parse JSON line: {e}")
                            continue
                        except Exception as e:
                            logger.error(f"Error processing event: {e}")
                            continue

                # Wait a bit before checking for new data
                await asyncio.sleep(0.1)

            except FileNotFoundError:
                logger.warning(f"Log file disappeared: {self.log_path}")
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Error in tail_alerts: {e}")
                await asyncio.sleep(1)

    async def get_recent_alerts(self, limit: int = 100) -> list[AlertEvent]:
        """
        Get recent alert events from the log file.

        Args:
            limit: Maximum number of alerts to return

        Returns:
            List of recent AlertEvent objects
        """
        alerts: list[AlertEvent] = []

        if not self.log_path.exists():
            return alerts

        try:
            with self.log_path.open(encoding="utf-8") as f:
                # Read file in reverse (last lines first)
                lines = f.readlines()
                for line in reversed(lines[-limit * 2 :]):  # Read more to account for non-alert events
                    if not line.strip():
                        continue

                    try:
                        event = json.loads(line)
                        if event.get("event_type") == "alert":
                            alert_data = event.get("alert", {})
                            alert_event = AlertEvent(
                                timestamp=datetime.fromisoformat(
                                    event.get("timestamp", "").replace("Z", "+00:00")
                                ),
                                event_type="alert",
                                src_ip=event.get("src_ip"),
                                dest_ip=event.get("dest_ip"),
                                alert=alert_data,
                                severity=alert_data.get("severity", 0),
                                signature=alert_data.get("signature", ""),
                            )
                            alerts.append(alert_event)

                            if len(alerts) >= limit:
                                break

                    except (json.JSONDecodeError, KeyError, ValueError):
                        continue

        except Exception as e:
            logger.error(f"Error reading recent alerts: {e}")

        return list(reversed(alerts))  # Return in chronological order
