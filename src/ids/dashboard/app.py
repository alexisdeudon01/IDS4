"""
FastAPI dashboard application for IDS monitoring.
"""

from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

import psutil
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .ai_healing import AIHealingService
from .elasticsearch import ElasticsearchMonitor
from .hardware import HardwareController
from .models import (
    AlertEvent,
    ElasticsearchHealth,
    NetworkStats,
    PipelineStatus,
    SystemHealth,
    TailscaleNode,
)
from .network import NetworkMonitor
from .suricata import SuricataLogMonitor
from .tailscale import TailscaleMonitor

logger = logging.getLogger(__name__)

# Global state
dashboard_state: dict[str, Any] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    # Startup
    logger.info("Starting IDS Dashboard...")

    # Initialize components
    dashboard_state["suricata"] = SuricataLogMonitor()
    await dashboard_state["suricata"].start()

    dashboard_state["elasticsearch"] = ElasticsearchMonitor(
        hosts=os.getenv("ELASTICSEARCH_HOSTS", "http://localhost:9200").split(","),
        username=os.getenv("ELASTICSEARCH_USERNAME"),
        password=os.getenv("ELASTICSEARCH_PASSWORD"),
    )
    await dashboard_state["elasticsearch"].connect()

    dashboard_state["network"] = NetworkMonitor(interface=os.getenv("MIRROR_INTERFACE", "eth0"))
    await dashboard_state["network"].ensure_promiscuous_mode()

    dashboard_state["hardware"] = HardwareController(led_pin=int(os.getenv("LED_PIN", "17")))

    dashboard_state["ai_healing"] = AIHealingService(api_key=os.getenv("ANTHROPIC_API_KEY"))

    tailnet = os.getenv("TAILSCALE_TAILNET")
    tailscale_api_key = os.getenv("TAILSCALE_API_KEY")
    if tailnet and tailscale_api_key:
        dashboard_state["tailscale"] = TailscaleMonitor(tailnet=tailnet, api_key=tailscale_api_key)
    else:
        dashboard_state["tailscale"] = None

    logger.info("IDS Dashboard started")

    yield

    # Shutdown
    logger.info("Shutting down IDS Dashboard...")

    if "suricata" in dashboard_state:
        await dashboard_state["suricata"].stop()

    if "elasticsearch" in dashboard_state:
        await dashboard_state["elasticsearch"].disconnect()

    if "hardware" in dashboard_state:
        dashboard_state["hardware"].cleanup()

    logger.info("IDS Dashboard stopped")


def create_dashboard_app() -> FastAPI:
    """Create and configure the FastAPI dashboard application."""
    app = FastAPI(
        title="IDS Dashboard",
        description="Professional monitoring dashboard for Raspberry Pi IDS",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify allowed origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # WebSocket endpoint for real-time alerts
    @app.websocket("/ws/alerts")
    async def websocket_alerts(websocket: WebSocket):
        """WebSocket endpoint for streaming Suricata alerts."""
        await websocket.accept()
        logger.info("WebSocket client connected for alerts")

        suricata = dashboard_state.get("suricata")
        hardware = dashboard_state.get("hardware")

        if not suricata:
            await websocket.send_json({"error": "Suricata monitor not available"})
            await websocket.close()
            return

        try:
            async for alert in suricata.tail_alerts():
                # Flash LED for critical alerts
                if hardware and alert.severity == 1:
                    hardware.handle_alert(alert.severity)

                # Send alert to client
                await websocket.send_json(alert.model_dump(mode="json"))

        except WebSocketDisconnect:
            logger.info("WebSocket client disconnected")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            await websocket.close()

    # REST API endpoints
    @app.get("/api/alerts/recent")
    async def get_recent_alerts(limit: int = 100) -> list[dict]:
        """Get recent Suricata alerts."""
        suricata = dashboard_state.get("suricata")
        if not suricata:
            return []

        alerts = await suricata.get_recent_alerts(limit=limit)
        return [alert.model_dump(mode="json") for alert in alerts]

    @app.get("/api/elasticsearch/health")
    async def get_elasticsearch_health() -> ElasticsearchHealth | None:
        """Get Elasticsearch cluster health."""
        es = dashboard_state.get("elasticsearch")
        if not es:
            return None

        return await es.get_cluster_health()

    @app.get("/api/network/stats")
    async def get_network_stats() -> NetworkStats | None:
        """Get network interface statistics."""
        network = dashboard_state.get("network")
        if not network:
            return None

        return await network.get_interface_stats()

    @app.get("/api/system/health")
    async def get_system_health() -> SystemHealth:
        """Get Raspberry Pi system health metrics."""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        # Get CPU temperature (Raspberry Pi)
        temperature = None
        try:
            temp_file = Path("/sys/class/thermal/thermal_zone0/temp")
            if temp_file.exists():
                temp_raw = temp_file.read_text().strip()
                temperature = float(temp_raw) / 1000.0  # Convert from millidegrees
        except Exception:
            pass

        boot_time = psutil.boot_time()
        import time

        uptime = time.time() - boot_time

        return SystemHealth(
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used=memory.used,
            memory_total=memory.total,
            disk_percent=disk.percent,
            disk_used=disk.used,
            disk_total=disk.total,
            temperature=temperature,
            uptime=uptime,
            timestamp=datetime.now(),
        )

    @app.get("/api/pipeline/status")
    async def get_pipeline_status() -> PipelineStatus:
        """Get pipeline component status."""

        # Check Suricata
        suricata_status = "unknown"
        try:
            result = await asyncio.to_thread(
                lambda: __import__("subprocess").run(
                    ["systemctl", "is-active", "suricata"],
                    capture_output=True,
                    text=True,
                )
            )
            suricata_status = "running" if result.returncode == 0 else "stopped"
        except Exception:
            suricata_status = "error"

        # Check Vector
        vector_status = "unknown"
        try:
            result = await asyncio.to_thread(
                lambda: __import__("subprocess").run(
                    ["systemctl", "is-active", "vector"],
                    capture_output=True,
                    text=True,
                )
            )
            vector_status = "running" if result.returncode == 0 else "stopped"
        except Exception:
            vector_status = "error"

        # Check Elasticsearch
        es = dashboard_state.get("elasticsearch")
        es_status = "unavailable"
        if es:
            health = await es.get_cluster_health()
            if health:
                es_status = health.status

        return PipelineStatus(
            interface=os.getenv("MIRROR_INTERFACE", "eth0"),
            suricata=suricata_status,
            vector=vector_status,
            elasticsearch=es_status,
            timestamp=datetime.now(),
        )

    @app.get("/api/tailscale/nodes")
    async def get_tailscale_nodes() -> list[TailscaleNode]:
        """Get Tailscale tailnet nodes."""
        tailscale = dashboard_state.get("tailscale")
        if not tailscale:
            return []

        return await tailscale.get_nodes()

    @app.post("/api/ai-healing/diagnose")
    async def diagnose_error(
        error_type: str,
        error_message: str,
        component: str | None = None,
    ) -> dict:
        """Diagnose an error using AI healing."""
        ai_healing = dashboard_state.get("ai_healing")
        if not ai_healing:
            return {"error": "AI healing service not available"}

        response = await ai_healing.diagnose_error(
            error_type=error_type,
            error_message=error_message,
            context={"component": component} if component else None,
        )

        return response.model_dump(mode="json")

    # Serve static frontend (if available)
    frontend_path = Path(__file__).parent.parent.parent.parent / "frontend" / "dist"
    if frontend_path.exists():
        app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")

        @app.get("/", response_class=HTMLResponse)
        async def serve_frontend():
            """Serve the frontend application."""
            index_file = frontend_path / "index.html"
            if index_file.exists():
                return index_file.read_text()
            return "<html><body><h1>IDS Dashboard</h1><p>Frontend not built. Run 'npm run build' in frontend directory.</p></body></html>"

    return app


# Create app instance
app = create_dashboard_app()
