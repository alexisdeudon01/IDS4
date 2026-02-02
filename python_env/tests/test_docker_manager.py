import unittest
import multiprocessing
import sys
import os
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'modules'))

from docker_manager import DockerManager
from config_manager import ConfigManager

class TestDockerManager(unittest.TestCase):
    
    def setUp(self):
        self.manager = multiprocessing.Manager()
        self.shared_state = self.manager.dict()
        self.config_manager = Mock(spec=ConfigManager)
        self.shutdown_event = multiprocessing.Event()
        
    @patch('docker.from_env')
    def test_initialization(self, mock_docker):
        mock_client = Mock()
        mock_docker.return_value = mock_client
        
        docker_manager = DockerManager(self.shared_state, self.config_manager)
        self.assertEqual(docker_manager.docker_client, mock_client)
        
    @patch('docker.from_env')
    def test_check_stack_health(self, mock_docker):
        mock_client = Mock()
        mock_container = Mock()
        mock_container.status = 'running'
        mock_container.attrs = {'State': {'Health': {'Status': 'healthy'}}}
        mock_client.containers.list.return_value = [mock_container]
        mock_docker.return_value = mock_client
        
        docker_manager = DockerManager(self.shared_state, self.config_manager)
        docker_manager.check_stack_health()
        
        self.assertTrue(self.shared_state.get('docker_healthy', False))

if __name__ == '__main__':
    unittest.main()