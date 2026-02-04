"""
Elasticsearch cluster health monitoring.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from elasticsearch import AsyncElasticsearch

from .models import ElasticsearchHealth

logger = logging.getLogger(__name__)


class ElasticsearchMonitor:
    """Monitor Elasticsearch cluster health and indices."""

    def __init__(
        self,
        hosts: list[str] | None = None,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        """
        Initialize Elasticsearch monitor.

        Args:
            hosts: List of Elasticsearch host URLs (default: ["http://localhost:9200"])
            username: Optional username for authentication
            password: Optional password for authentication
        """
        self.hosts = hosts or ["http://localhost:9200"]
        self.username = username
        self.password = password
        self._client: AsyncElasticsearch | None = None

    async def connect(self) -> None:
        """Establish connection to Elasticsearch."""
        try:
            auth = None
            if self.username and self.password:
                auth = (self.username, self.password)

            self._client = AsyncElasticsearch(
                hosts=self.hosts,
                basic_auth=auth,
                request_timeout=10,
            )

            # Test connection
            info = await self._client.info()
            logger.info(f"Connected to Elasticsearch: {info.get('cluster_name', 'unknown')}")

        except Exception as e:
            logger.error(f"Failed to connect to Elasticsearch: {e}")
            self._client = None

    async def disconnect(self) -> None:
        """Close Elasticsearch connection."""
        if self._client:
            await self._client.close()
            self._client = None
            logger.info("Disconnected from Elasticsearch")

    async def get_cluster_health(self) -> ElasticsearchHealth | None:
        """
        Get Elasticsearch cluster health status.

        Returns:
            ElasticsearchHealth object or None if unavailable
        """
        if not self._client:
            await self.connect()

        if not self._client:
            return None

        try:
            health_response = await self._client.cluster.health()
            indices_response = await self._client.cat.indices(
                format="json",
                h="index,creation.date",
            )

            # Count daily indices (indices created today)
            today = datetime.now().date()
            daily_count = 0

            for idx in indices_response:
                index_name = idx.get("index", "")
                # Check if index matches daily pattern (e.g., logstash-2024.01.15)
                if "." in index_name:
                    try:
                        # Try to extract date from index name
                        parts = index_name.split(".")
                        if len(parts) >= 3:
                            year = int(parts[-3])
                            month = int(parts[-2])
                            day = int(parts[-1])
                            index_date = datetime(year, month, day).date()
                            if index_date == today:
                                daily_count += 1
                    except (ValueError, IndexError):
                        continue

            return ElasticsearchHealth(
                status=health_response.get("status", "unknown"),
                cluster_name=health_response.get("cluster_name", "unknown"),
                number_of_nodes=health_response.get("number_of_nodes", 0),
                number_of_data_nodes=health_response.get("number_of_data_nodes", 0),
                active_primary_shards=health_response.get("active_primary_shards", 0),
                active_shards=health_response.get("active_shards", 0),
                relocating_shards=health_response.get("relocating_shards", 0),
                initializing_shards=health_response.get("initializing_shards", 0),
                unassigned_shards=health_response.get("unassigned_shards", 0),
                daily_indices_count=daily_count,
            )

        except Exception as e:
            logger.error(f"Error getting cluster health: {e}")
            return None

    async def get_index_stats(self, index_pattern: str = "logstash-*") -> dict[str, Any]:
        """
        Get statistics for indices matching a pattern.

        Args:
            index_pattern: Index pattern (e.g., "logstash-*")

        Returns:
            Dictionary with index statistics
        """
        if not self._client:
            await self.connect()

        if not self._client:
            return {}

        try:
            stats = await self._client.indices.stats(index=index_pattern)
            return stats

        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            return {}
