#!/usr/bin/env python3
"""
Standalone script to monitor and visualize Tailscale mesh network.

Usage:
    python scripts/monitor_tailnet.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ids.monitoring.tailnet_monitor import run_interactive_monitor

if __name__ == "__main__":
    run_interactive_monitor()
