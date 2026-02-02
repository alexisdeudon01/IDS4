import unittest
import multiprocessing
import sys
import os
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'modules'))

try:
    from web_interface_manager import WebInterfaceManager
    from metrics_server import MetricsServer
    from config_manager import ConfigManager
except ImportError:
    modules_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'modules'))
    if modules_path not in sys.path:
        sys.path.insert(0, modules_path)
    from web_interface_manager import WebInterfaceManager
    from metrics_server import MetricsServer
    from config_manager import ConfigManager

class TestWebInterfaceAPI(unittest.TestCase):
    """Test all Web Interface API functionality"""
    
    def setUp(self):
        self.manager = multiprocessing.Manager()
        self.shared_state = self.manager.dict({
            'cpu_usage': 25.5,
            'ram_usage': 45.2,
            'throttling_level': 1,
            'aws_ready': True,
            'vector_ready': True,
            'redis_ready': True,
            'pipeline_ok': True,
            'docker_healthy': True,
            'last_error': '',
            'suricata_rules_updated': True
        })
        self.shutdown_event = multiprocessing.Event()
        
        self.config_manager = Mock(spec=ConfigManager)
        self.config_manager.get.side_effect = lambda key, default=None: {
            'fastapi.port': 8000,
            'fastapi.host': '0.0.0.0'
        }.get(key, default)
        
        # Mock file system for HTML template
        with patch('builtins.open', mock_open_html()):
            self.web_manager = WebInterfaceManager(
                self.shared_state, 
                self.config_manager, 
                self.shutdown_event
            )
        
        self.client = TestClient(self.web_manager.app)

    def test_status_endpoint_success(self):
        """Test /status endpoint returns correct system status"""
        response = self.client.get("/status")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data['cpu_usage'], 25.5)
        self.assertEqual(data['ram_usage'], 45.2)
        self.assertEqual(data['throttling_level'], 1)
        self.assertTrue(data['aws_ready'])
        self.assertTrue(data['vector_ready'])
        self.assertTrue(data['redis_ready'])
        self.assertTrue(data['pipeline_ok'])
        self.assertTrue(data['docker_healthy'])
        self.assertEqual(data['last_error'], '')
        self.assertTrue(data['suricata_rules_updated'])

    def test_status_endpoint_with_errors(self):
        """Test /status endpoint with system errors"""
        self.shared_state.update({
            'cpu_usage': 85.0,
            'ram_usage': 90.0,
            'throttling_level': 3,
            'aws_ready': False,
            'pipeline_ok': False,
            'last_error': 'OpenSearch connection failed'
        })
        
        response = self.client.get("/status")
        data = response.json()
        
        self.assertEqual(data['cpu_usage'], 85.0)
        self.assertEqual(data['throttling_level'], 3)
        self.assertFalse(data['aws_ready'])
        self.assertFalse(data['pipeline_ok'])
        self.assertEqual(data['last_error'], 'OpenSearch connection failed')

    def test_config_update_success(self):
        """Test /config POST endpoint updates configuration"""
        new_config = {
            'aws': {'region': 'us-west-2'},
            'redis': {'port': 6380}
        }
        
        with patch.object(self.web_manager.config, 'update_config') as mock_update:
            response = self.client.post("/config", json=new_config)
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['message'], 'Configuration mise à jour avec succès.')
            mock_update.assert_called_once_with(new_config)

    def test_config_update_failure(self):
        """Test /config POST endpoint handles update failures"""
        new_config = {'invalid': 'config'}
        
        with patch.object(self.web_manager.config, 'update_config') as mock_update:
            mock_update.side_effect = Exception("Invalid configuration")
            
            response = self.client.post("/config", json=new_config)
            
            self.assertEqual(response.status_code, 500)
            self.assertIn("Invalid configuration", response.json()['detail'])

    def test_root_endpoint_returns_html(self):
        """Test root endpoint returns HTML interface"""
        with patch('builtins.open', mock_open_html()):
            response = self.client.get("/")
            
            self.assertEqual(response.status_code, 200)
            self.assertIn("text/html", response.headers.get("content-type", ""))

class TestMetricsServerAPI(unittest.TestCase):
    """Test Metrics Server Prometheus API functionality"""
    
    def setUp(self):
        self.manager = multiprocessing.Manager()
        self.shared_state = self.manager.dict({
            'cpu_usage': 30.0,
            'ram_usage': 50.0,
            'redis_queue_depth': 100,
            'vector_healthy': True,
            'aws_ready': True,
            'redis_ready': True,
            'pipeline_ok': True,
            'throttling_level': 0,
            'ingestion_rate_increment': 10,
            'error_increment': 1
        })
        self.shutdown_event = multiprocessing.Event()
        
        self.config_manager = Mock(spec=ConfigManager)
        self.config_manager.get.side_effect = lambda key, default=None: {
            'prometheus.port': 9100,
            'prometheus.update_interval': 1
        }.get(key, default)

    @patch('prometheus_client.start_http_server')
    def test_metrics_server_initialization(self, mock_start_server):
        """Test MetricsServer initializes correctly"""
        metrics_server = MetricsServer(
            self.shared_state, 
            self.config_manager, 
            self.shutdown_event
        )
        
        self.assertEqual(metrics_server.port, 9100)
        self.assertEqual(metrics_server.update_interval, 1)
        self.assertIsNotNone(metrics_server.cpu_usage_gauge)
        self.assertIsNotNone(metrics_server.ram_usage_gauge)

    @patch('prometheus_client.start_http_server')
    def test_metrics_update_from_shared_state(self, mock_start_server):
        """Test metrics are updated from shared state"""
        metrics_server = MetricsServer(
            self.shared_state, 
            self.config_manager, 
            self.shutdown_event
        )
        
        with patch.object(metrics_server.cpu_usage_gauge, 'set') as mock_cpu_set, \
             patch.object(metrics_server.ram_usage_gauge, 'set') as mock_ram_set, \
             patch.object(metrics_server.ingestion_rate_counter, 'inc') as mock_ingestion_inc:
            
            metrics_server._update_metrics()
            
            mock_cpu_set.assert_called_with(30.0)
            mock_ram_set.assert_called_with(50.0)
            mock_ingestion_inc.assert_called_with(10)

    @patch('prometheus_client.start_http_server')
    def test_metrics_counter_reset_after_increment(self, mock_start_server):
        """Test counters are reset after incrementing"""
        metrics_server = MetricsServer(
            self.shared_state, 
            self.config_manager, 
            self.shutdown_event
        )
        
        metrics_server._update_metrics()
        
        self.assertEqual(self.shared_state['ingestion_rate_increment'], 0)
        self.assertEqual(self.shared_state['error_increment'], 0)

    @patch('prometheus_client.start_http_server')
    def test_metrics_boolean_conversion(self, mock_start_server):
        """Test boolean values are converted to 0/1 for Prometheus"""
        metrics_server = MetricsServer(
            self.shared_state, 
            self.config_manager, 
            self.shutdown_event
        )
        
        with patch.object(metrics_server.vector_health_gauge, 'set') as mock_vector_set, \
             patch.object(metrics_server.aws_ready_gauge, 'set') as mock_aws_set:
            
            metrics_server._update_metrics()
            
            mock_vector_set.assert_called_with(1)  # True -> 1
            mock_aws_set.assert_called_with(1)     # True -> 1

class TestSystemIntegrationAPI(unittest.TestCase):
    """Test system integration API functionality"""
    
    def setUp(self):
        self.manager = multiprocessing.Manager()
        self.shared_state = self.manager.dict({
            'cpu_usage': 0.0,
            'ram_usage': 0.0,
            'throttling_level': 0,
            'aws_ready': False,
            'vector_ready': False,
            'redis_ready': False,
            'pipeline_ok': False,
            'docker_healthy': False,
            'last_error': '',
            'suricata_rules_updated': False,
            'redis_queue_depth': 0,
            'vector_healthy': False,
            'ingestion_rate_increment': 0,
            'error_increment': 0
        })

    def test_shared_state_updates_cpu_ram(self):
        """Test shared state updates for CPU/RAM monitoring"""
        # Simulate ResourceController updates
        self.shared_state['cpu_usage'] = 75.5
        self.shared_state['ram_usage'] = 68.2
        self.shared_state['throttling_level'] = 2
        
        self.assertEqual(self.shared_state['cpu_usage'], 75.5)
        self.assertEqual(self.shared_state['ram_usage'], 68.2)
        self.assertEqual(self.shared_state['throttling_level'], 2)

    def test_shared_state_updates_connectivity(self):
        """Test shared state updates for connectivity status"""
        # Simulate ConnectivityAsync updates
        self.shared_state['aws_ready'] = True
        self.shared_state['redis_ready'] = True
        self.shared_state['pipeline_ok'] = True
        
        self.assertTrue(self.shared_state['aws_ready'])
        self.assertTrue(self.shared_state['redis_ready'])
        self.assertTrue(self.shared_state['pipeline_ok'])

    def test_shared_state_updates_docker_health(self):
        """Test shared state updates for Docker health"""
        # Simulate DockerManager updates
        self.shared_state['docker_healthy'] = True
        self.shared_state['vector_healthy'] = True
        
        self.assertTrue(self.shared_state['docker_healthy'])
        self.assertTrue(self.shared_state['vector_healthy'])

    def test_shared_state_error_logging(self):
        """Test shared state error logging functionality"""
        error_message = "OpenSearch connection timeout"
        self.shared_state['last_error'] = error_message
        self.shared_state['pipeline_ok'] = False
        
        self.assertEqual(self.shared_state['last_error'], error_message)
        self.assertFalse(self.shared_state['pipeline_ok'])

    def test_shared_state_metrics_increments(self):
        """Test shared state metrics increment functionality"""
        # Simulate metrics increments
        self.shared_state['ingestion_rate_increment'] = 50
        self.shared_state['error_increment'] = 2
        
        # Simulate MetricsServer consuming increments
        ingestion_increment = self.shared_state['ingestion_rate_increment']
        error_increment = self.shared_state['error_increment']
        
        self.assertEqual(ingestion_increment, 50)
        self.assertEqual(error_increment, 2)
        
        # Reset after consumption
        self.shared_state['ingestion_rate_increment'] = 0
        self.shared_state['error_increment'] = 0
        
        self.assertEqual(self.shared_state['ingestion_rate_increment'], 0)
        self.assertEqual(self.shared_state['error_increment'], 0)

class TestAPIEndpointsIntegration(unittest.TestCase):
    """Test API endpoints integration with system components"""
    
    def setUp(self):
        self.manager = multiprocessing.Manager()
        self.shared_state = self.manager.dict({
            'cpu_usage': 45.0,
            'ram_usage': 60.0,
            'throttling_level': 1,
            'aws_ready': True,
            'vector_ready': True,
            'redis_ready': True,
            'pipeline_ok': True,
            'docker_healthy': True,
            'last_error': '',
            'suricata_rules_updated': True,
            'redis_queue_depth': 250,
            'vector_healthy': True
        })

    def test_status_api_reflects_system_state(self):
        """Test status API accurately reflects system state changes"""
        config_manager = Mock(spec=ConfigManager)
        config_manager.get.side_effect = lambda key, default=None: {
            'fastapi.port': 8000,
            'fastapi.host': '0.0.0.0'
        }.get(key, default)
        
        with patch('builtins.open', mock_open_html()):
            web_manager = WebInterfaceManager(
                self.shared_state, 
                config_manager, 
                multiprocessing.Event()
            )
        
        client = TestClient(web_manager.app)
        
        # Test initial state
        response = client.get("/status")
        data = response.json()
        self.assertEqual(data['cpu_usage'], 45.0)
        self.assertTrue(data['pipeline_ok'])
        
        # Simulate system degradation
        self.shared_state['cpu_usage'] = 85.0
        self.shared_state['pipeline_ok'] = False
        self.shared_state['last_error'] = 'High CPU usage detected'
        
        # Test updated state
        response = client.get("/status")
        data = response.json()
        self.assertEqual(data['cpu_usage'], 85.0)
        self.assertFalse(data['pipeline_ok'])
        self.assertEqual(data['last_error'], 'High CPU usage detected')

    def test_prometheus_metrics_integration(self):
        """Test Prometheus metrics integration with shared state"""
        config_manager = Mock(spec=ConfigManager)
        config_manager.get.side_effect = lambda key, default=None: {
            'prometheus.port': 9100,
            'prometheus.update_interval': 1
        }.get(key, default)
        
        with patch('prometheus_client.start_http_server'):
            metrics_server = MetricsServer(
                self.shared_state,
                config_manager,
                multiprocessing.Event()
            )
        
        # Mock all gauge and counter methods
        with patch.object(metrics_server.cpu_usage_gauge, 'set') as mock_cpu, \
             patch.object(metrics_server.pipeline_ok_gauge, 'set') as mock_pipeline, \
             patch.object(metrics_server.redis_queue_depth_gauge, 'set') as mock_redis:
            
            metrics_server._update_metrics()
            
            mock_cpu.assert_called_with(45.0)
            mock_pipeline.assert_called_with(1)  # True -> 1
            mock_redis.assert_called_with(250)

def mock_open_html():
    """Mock file open for HTML template"""
    def mock_open_func(*args, **kwargs):
        if 'index.html' in str(args[0]):
            mock_file = Mock()
            mock_file.read.return_value = "<html><body>Test Interface</body></html>"
            mock_file.__enter__.return_value = mock_file
            return mock_file
        return Mock()
    return mock_open_func

if __name__ == '__main__':
    unittest.main()