import unittest
import multiprocessing
import tempfile
import sys
import os
import yaml
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from main import AgentSupervisor

class TestAgentSupervisor(unittest.TestCase):
    
    def setUp(self):
        self.test_config = {
            'raspberry_pi': {
                'ip': '192.168.178.66',
                'cpu_limit_percent': 70,
                'ram_limit_percent': 70
            },
            'prometheus': {
                'port': 9100,
                'update_interval': 5
            },
            'fastapi': {
                'port': 8000,
                'host': '0.0.0.0'
            }
        }
        
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(self.test_config, f)
            self.config_path = f.name
            
    def tearDown(self):
        os.unlink(self.config_path)
        
    def test_initialization(self):
        supervisor = AgentSupervisor(self.config_path)
        self.assertIsNotNone(supervisor.config_manager)
        self.assertIsNotNone(supervisor.shared_state)
        self.assertIsNotNone(supervisor.shutdown_event)
        self.assertEqual(len(supervisor.processes), 0)
        
    @patch('main.multiprocessing.Process')
    def test_start_child_process(self, mock_process):
        mock_instance = Mock()
        mock_process_obj = Mock()
        mock_process.return_value = mock_process_obj
        
        supervisor = AgentSupervisor(self.config_path)
        
        # Mock the target class
        mock_class = Mock(return_value=mock_instance)
        process = supervisor._start_child_process("TestProcess", mock_class)
        
        mock_class.assert_called_once()
        mock_process_obj.start.assert_called_once()
        self.assertEqual(len(supervisor.processes), 1)
        
    def test_graceful_shutdown(self):
        supervisor = AgentSupervisor(self.config_path)
        supervisor._graceful_shutdown()
        self.assertTrue(supervisor.shutdown_event.is_set())

if __name__ == '__main__':
    unittest.main()