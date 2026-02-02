import unittest
import multiprocessing
import sys
import os
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'modules'))

from metrics_server import MetricsServer
from config_manager import ConfigManager

class TestMetricsServer(unittest.TestCase):
    
    def setUp(self):
        self.manager = multiprocessing.Manager()
        self.shared_state = self.manager.dict({
            'cpu_usage': 25.5,
            'ram_usage': 40.2,
            'redis_queue_depth': 100,
            'vector_healthy': True,
            'aws_ready': True,
            'pipeline_ok': True
        })
        self.config_manager = Mock(spec=ConfigManager)
        self.config_manager.get.side_effect = lambda key, default: {
            'prometheus.port': 9100,
            'prometheus.update_interval': 5
        }.get(key, default)
        self.shutdown_event = multiprocessing.Event()
        
    def test_initialization(self):
        metrics_server = MetricsServer(self.shared_state, self.config_manager, self.shutdown_event)
        self.assertEqual(metrics_server.port, 9100)
        self.assertEqual(metrics_server.update_interval, 5)
        
    def test_update_metrics(self):
        metrics_server = MetricsServer(self.shared_state, self.config_manager, self.shutdown_event)
        metrics_server._update_metrics()
        # Verify metrics are updated from shared state
        self.assertEqual(metrics_server.cpu_usage_gauge._value._value, 25.5)
        self.assertEqual(metrics_server.ram_usage_gauge._value._value, 40.2)

if __name__ == '__main__':
    unittest.main()