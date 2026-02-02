import unittest
import multiprocessing
import sys
import os
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'modules'))

from resource_controller import ResourceController
from config_manager import ConfigManager

class TestResourceController(unittest.TestCase):
    
    def setUp(self):
        self.manager = multiprocessing.Manager()
        self.shared_state = self.manager.dict()
        self.config_manager = Mock(spec=ConfigManager)
        self.config_manager.get.side_effect = lambda key, default: {
            'raspberry_pi.cpu_limit_percent': 70,
            'raspberry_pi.ram_limit_percent': 70
        }.get(key, default)
        self.shutdown_event = multiprocessing.Event()
        
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    def test_monitor_resources(self, mock_memory, mock_cpu):
        mock_cpu.return_value = 45.5
        mock_memory.return_value.percent = 60.2
        
        controller = ResourceController(self.shared_state, self.config_manager, self.shutdown_event)
        controller._monitor_resources()
        
        self.assertEqual(self.shared_state['cpu_usage'], 45.5)
        self.assertEqual(self.shared_state['ram_usage'], 60.2)
        
    def test_calculate_throttling_level(self):
        controller = ResourceController(self.shared_state, self.config_manager, self.shutdown_event)
        
        # Normal usage
        level = controller._calculate_throttling_level(50, 50)
        self.assertEqual(level, 0)
        
        # High usage
        level = controller._calculate_throttling_level(75, 75)
        self.assertEqual(level, 2)

if __name__ == '__main__':
    unittest.main()