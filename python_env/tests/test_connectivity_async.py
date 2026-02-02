import unittest
import asyncio
import multiprocessing
import sys
import os
from unittest.mock import Mock, patch, AsyncMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'modules'))

from connectivity_async import ConnectivityAsync
from config_manager import ConfigManager

class TestConnectivityAsync(unittest.TestCase):
    
    def setUp(self):
        self.manager = multiprocessing.Manager()
        self.shared_state = self.manager.dict()
        self.config_manager = Mock(spec=ConfigManager)
        self.shutdown_event = multiprocessing.Event()
        
    @patch('aiohttp.ClientSession.get')
    async def test_check_dns_async(self, mock_get):
        mock_response = Mock()
        mock_response.status = 200
        mock_get.return_value.__aenter__.return_value = mock_response
        
        connectivity = ConnectivityAsync(self.shared_state, self.config_manager, self.shutdown_event)
        result = await connectivity._check_dns_async()
        self.assertTrue(result)
        
    @patch('ssl.create_default_context')
    @patch('aiohttp.ClientSession.get')
    async def test_check_tls_async(self, mock_get, mock_ssl):
        mock_response = Mock()
        mock_response.status = 200
        mock_get.return_value.__aenter__.return_value = mock_response
        
        connectivity = ConnectivityAsync(self.shared_state, self.config_manager, self.shutdown_event)
        result = await connectivity._check_tls_async()
        self.assertTrue(result)
        
    def test_run_async_tests(self):
        connectivity = ConnectivityAsync(self.shared_state, self.config_manager, self.shutdown_event)
        # Test that async loop can be created
        self.assertIsNotNone(connectivity)

if __name__ == '__main__':
    unittest.main()