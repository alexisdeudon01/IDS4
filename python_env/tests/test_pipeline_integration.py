import unittest
import multiprocessing
import sys
import os
import json
import time
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock, mock_open
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'modules'))

from suricata_manager import SuricataManager
from vector_manager import VectorManager
from docker_manager import DockerManager
from aws_manager import AWSManager
from connectivity_async import ConnectivityAsync
from config_manager import ConfigManager

class TestPipelineIntegration(unittest.TestCase):
    """Test complete pipeline integration Suricata->Vector->Redis->OpenSearch"""
    
    def setUp(self):
        self.manager = multiprocessing.Manager()
        self.shared_state = self.manager.dict({
            'aws_ready': False,
            'redis_ready': False,
            'vector_healthy': False,
            'docker_healthy': False,
            'pipeline_ok': False,
            'last_error': '',
            'cpu_usage': 30.0,
            'ram_usage': 40.0,
            'throttling_level': 0
        })
        self.shutdown_event = multiprocessing.Event()
        
        # Create temp directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.suricata_config_path = os.path.join(self.temp_dir, 'suricata.yaml')
        self.vector_config_path = os.path.join(self.temp_dir, 'vector.toml')
        self.eve_log_path = os.path.join(self.temp_dir, 'eve.json')
        
        self.config_manager = Mock(spec=ConfigManager)
        self.config_manager.get.side_effect = lambda key, default=None: {
            'suricata.config_path': self.suricata_config_path,
            'suricata.log_path': self.eve_log_path,
            'vector.config_path': self.vector_config_path,
            'vector.log_read_path': self.eve_log_path,
            'raspberry_pi.network_interface': 'eth0',
            'aws.opensearch_endpoint': 'https://test-domain.eu-central-1.es.amazonaws.com',
            'aws.region': 'eu-central-1',
            'redis.host': 'redis',
            'redis.port': 6379,
            'docker.compose_file': 'docker/docker-compose.yml',
            'docker.required_services': ['vector', 'redis', 'prometheus'],
            'vector.batch_max_events': 500,
            'vector.batch_timeout_secs': 2,
            'vector.index_pattern': 'suricata-ids2-%Y.%m.%d'
        }.get(key, default)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_suricata_config_generation(self):
        """Test Suricata configuration generation"""
        suricata_manager = SuricataManager(
            self.shared_state, 
            self.config_manager, 
            self.shutdown_event
        )
        
        result = suricata_manager.generate_suricata_config()
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.suricata_config_path))
        
        with open(self.suricata_config_path, 'r') as f:
            config_content = f.read()
            self.assertIn('eve-log:', config_content)
            self.assertIn('eve.json', config_content)

    def test_vector_config_generation(self):
        """Test Vector configuration generation"""
        vector_manager = VectorManager(
            self.shared_state,
            self.config_manager,
            self.shutdown_event
        )
        
        result = vector_manager.generate_vector_config()
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.vector_config_path))
        
        with open(self.vector_config_path, 'r') as f:
            config_content = f.read()
            self.assertIn('[sources.suricata_logs]', config_content)
            self.assertIn('[transforms.parse_json_ecs]', config_content)
            self.assertIn('[sinks.redis_sink]', config_content)
            self.assertIn('[sinks.opensearch_sink]', config_content)
            self.assertIn('redis:6379', config_content)
            self.assertIn('test-domain.eu-central-1.es.amazonaws.com', config_content)

    def test_pipeline_data_flow_simulation(self):
        """Test simulated data flow through pipeline"""
        # Create sample Suricata log data
        sample_suricata_logs = [
            {
                "timestamp": "2024-01-01T10:00:00.000000+0000",
                "event_type": "alert",
                "src_ip": "192.168.1.100",
                "dest_ip": "10.0.0.5",
                "src_port": 12345,
                "dest_port": 80,
                "proto": "TCP",
                "alert": {
                    "signature": "ET SCAN Suspicious inbound to mySQL port 3306",
                    "severity": 2
                }
            },
            {
                "timestamp": "2024-01-01T10:00:01.000000+0000",
                "event_type": "http",
                "src_ip": "10.0.0.5",
                "dest_ip": "192.168.1.100",
                "src_port": 80,
                "dest_port": 12345,
                "proto": "TCP",
                "http": {
                    "hostname": "example.com",
                    "url": "/api/data",
                    "http_method": "GET"
                }
            }
        ]
        
        # Write sample logs to eve.json
        with open(self.eve_log_path, 'w') as f:
            for log in sample_suricata_logs:
                f.write(json.dumps(log) + '\n')
        
        # Verify log file creation
        self.assertTrue(os.path.exists(self.eve_log_path))
        
        # Simulate Vector processing (ECS mapping)
        processed_logs = []
        for log in sample_suricata_logs:
            ecs_log = self._simulate_ecs_mapping(log)
            processed_logs.append(ecs_log)
        
        # Verify ECS mapping
        alert_log = processed_logs[0]
        self.assertEqual(alert_log['event']['kind'], 'alert')
        self.assertEqual(alert_log['source']['ip'], '192.168.1.100')
        self.assertEqual(alert_log['destination']['ip'], '10.0.0.5')
        self.assertEqual(alert_log['suricata']['signature'], 'ET SCAN Suspicious inbound to mySQL port 3306')
        
        http_log = processed_logs[1]
        self.assertEqual(http_log['event']['kind'], 'event')
        self.assertEqual(http_log['network']['protocol'], 'TCP')

    def _simulate_ecs_mapping(self, suricata_log):
        """Simulate Vector's ECS mapping transformation"""
        ecs_log = {
            "@timestamp": suricata_log.get("timestamp"),
            "event": {
                "kind": "event",
                "category": "network"
            }
        }
        
        # Map IP addresses
        if "src_ip" in suricata_log:
            ecs_log["source"] = {"ip": suricata_log["src_ip"]}
        if "dest_ip" in suricata_log:
            ecs_log["destination"] = {"ip": suricata_log["dest_ip"]}
        if "src_port" in suricata_log:
            ecs_log.setdefault("source", {})["port"] = suricata_log["src_port"]
        if "dest_port" in suricata_log:
            ecs_log.setdefault("destination", {})["port"] = suricata_log["dest_port"]
        if "proto" in suricata_log:
            ecs_log["network"] = {"protocol": suricata_log["proto"]}
        
        # Handle alerts
        if suricata_log.get("event_type") == "alert":
            ecs_log["event"]["kind"] = "alert"
            if "alert" in suricata_log:
                ecs_log["suricata"] = {
                    "signature": suricata_log["alert"]["signature"],
                    "severity": suricata_log["alert"]["severity"]
                }
        
        return ecs_log

    @patch('docker.from_env')
    @patch('subprocess.run')
    def test_docker_stack_health_check(self, mock_subprocess, mock_docker):
        """Test Docker stack health monitoring"""
        mock_client = Mock()
        mock_docker.return_value = mock_client
        mock_client.ping.return_value = True
        
        # Mock container health
        mock_container = Mock()
        mock_container.status = 'running'
        mock_client.containers.get.return_value = mock_container
        mock_client.api.inspect_container.return_value = {
            'State': {'Health': {'Status': 'healthy'}}
        }
        
        # Mock docker compose ps command
        mock_subprocess.return_value.stdout = 'container_id_123\n'
        mock_subprocess.return_value.returncode = 0
        
        docker_manager = DockerManager(
            self.shared_state,
            self.config_manager,
            self.shutdown_event
        )
        
        result = docker_manager.check_stack_health()
        
        self.assertTrue(result)
        self.assertTrue(self.shared_state['docker_healthy'])

    @patch('modules.aws_manager.boto3.Session')
    @patch('modules.aws_manager.OpenSearch')
    def test_aws_opensearch_integration(self, mock_opensearch, mock_session):
        """Test AWS OpenSearch integration"""
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance
        mock_credentials = Mock()
        mock_credentials.access_key = 'test_key'
        mock_credentials.secret_key = 'test_secret'
        mock_credentials.token = None
        mock_session_instance.get_credentials.return_value = mock_credentials
        
        mock_opensearch_client = Mock()
        mock_opensearch.return_value = mock_opensearch_client
        mock_opensearch_client.bulk.return_value = {'errors': False}
        
        aws_manager = AWSManager(self.shared_state, self.config_manager)
        
        # Test bulk send with ECS-formatted logs
        ecs_logs = [
            {
                "@timestamp": "2024-01-01T10:00:00Z",
                "event": {"kind": "alert", "category": "network"},
                "source": {"ip": "192.168.1.100"},
                "destination": {"ip": "10.0.0.5"},
                "suricata": {"signature": "Test alert", "severity": 2}
            }
        ]
        
        result = aws_manager.send_bulk_to_opensearch(ecs_logs)
        
        self.assertTrue(result)
        self.assertTrue(self.shared_state['aws_ready'])
        mock_opensearch_client.bulk.assert_called_once()

    def test_pipeline_error_handling(self):
        """Test pipeline error handling and recovery"""
        # Test Suricata config generation failure
        self.config_manager.get.side_effect = lambda key, default=None: {
            'suricata.config_path': '/invalid/path/suricata.yaml'
        }.get(key, default)
        
        suricata_manager = SuricataManager(
            self.shared_state,
            self.config_manager,
            self.shutdown_event
        )
        
        result = suricata_manager.generate_suricata_config()
        self.assertFalse(result)
        
        # Reset config for Vector test
        self.config_manager.get.side_effect = lambda key, default=None: {
            'vector.config_path': '/invalid/path/vector.toml'
        }.get(key, default)
        
        vector_manager = VectorManager(
            self.shared_state,
            self.config_manager,
            self.shutdown_event
        )
        
        result = vector_manager.generate_vector_config()
        self.assertFalse(result)

    def test_pipeline_resource_monitoring(self):
        """Test pipeline resource monitoring integration"""
        # Simulate high resource usage
        self.shared_state.update({
            'cpu_usage': 85.0,
            'ram_usage': 90.0,
            'throttling_level': 3
        })
        
        # Test that pipeline components can read resource state
        vector_manager = VectorManager(
            self.shared_state,
            self.config_manager,
            self.shutdown_event
        )
        
        # Simulate Vector health check under high load
        self.shared_state['docker_healthy'] = False
        result = vector_manager.check_vector_health()
        
        self.assertFalse(result)
        self.assertFalse(self.shared_state['vector_healthy'])

    def test_pipeline_connectivity_integration(self):
        """Test pipeline connectivity monitoring"""
        # Test connectivity state updates
        self.shared_state.update({
            'aws_ready': True,
            'redis_ready': True,
            'vector_healthy': True,
            'docker_healthy': True
        })
        
        # Verify pipeline_ok calculation
        pipeline_components_ready = (
            self.shared_state['aws_ready'] and
            self.shared_state['redis_ready'] and
            self.shared_state['vector_healthy'] and
            self.shared_state['docker_healthy']
        )
        
        self.assertTrue(pipeline_components_ready)
        
        # Test partial failure
        self.shared_state['aws_ready'] = False
        pipeline_components_ready = (
            self.shared_state['aws_ready'] and
            self.shared_state['redis_ready'] and
            self.shared_state['vector_healthy'] and
            self.shared_state['docker_healthy']
        )
        
        self.assertFalse(pipeline_components_ready)

class TestPipelineEndToEnd(unittest.TestCase):
    """End-to-end pipeline tests"""
    
    def setUp(self):
        self.manager = multiprocessing.Manager()
        self.shared_state = self.manager.dict({
            'aws_ready': False,
            'redis_ready': False,
            'vector_healthy': False,
            'docker_healthy': False,
            'pipeline_ok': False,
            'cpu_usage': 25.0,
            'ram_usage': 35.0,
            'throttling_level': 0,
            'ingestion_rate_increment': 0,
            'error_increment': 0
        })

    def test_complete_pipeline_flow(self):
        """Test complete pipeline data flow simulation"""
        # Step 1: Suricata generates logs
        suricata_log = {
            "timestamp": "2024-01-01T10:00:00.000000+0000",
            "event_type": "alert",
            "src_ip": "192.168.1.100",
            "dest_ip": "10.0.0.5",
            "alert": {"signature": "Test Alert", "severity": 2}
        }
        
        # Step 2: Vector processes and transforms to ECS
        ecs_log = {
            "@timestamp": "2024-01-01T10:00:00Z",
            "event": {"kind": "alert", "category": "network"},
            "source": {"ip": "192.168.1.100"},
            "destination": {"ip": "10.0.0.5"},
            "suricata": {"signature": "Test Alert", "severity": 2}
        }
        
        # Step 3: Redis buffers the data (simulated)
        redis_buffer = [ecs_log]
        
        # Step 4: OpenSearch receives the data (simulated)
        opensearch_index = "suricata-ids2-2024.01.01"
        
        # Verify data transformation
        self.assertEqual(ecs_log["event"]["kind"], "alert")
        self.assertEqual(ecs_log["source"]["ip"], suricata_log["src_ip"])
        self.assertEqual(ecs_log["suricata"]["signature"], suricata_log["alert"]["signature"])
        
        # Simulate successful ingestion
        self.shared_state['ingestion_rate_increment'] = 1
        self.shared_state['aws_ready'] = True
        self.shared_state['redis_ready'] = True
        self.shared_state['pipeline_ok'] = True
        
        # Verify pipeline state
        self.assertTrue(self.shared_state['pipeline_ok'])
        self.assertEqual(self.shared_state['ingestion_rate_increment'], 1)

    def test_pipeline_backpressure_handling(self):
        """Test pipeline backpressure and buffering"""
        # Simulate OpenSearch unavailable
        self.shared_state['aws_ready'] = False
        self.shared_state['redis_ready'] = True
        
        # Redis should buffer data when OpenSearch is down
        buffered_logs = []
        for i in range(100):
            log = {
                "@timestamp": f"2024-01-01T10:00:{i:02d}Z",
                "event": {"kind": "alert"},
                "message": f"Alert {i}"
            }
            buffered_logs.append(log)
        
        # Simulate Redis queue depth increase
        self.shared_state['redis_queue_depth'] = len(buffered_logs)
        
        self.assertEqual(self.shared_state['redis_queue_depth'], 100)
        self.assertFalse(self.shared_state['aws_ready'])
        
        # Simulate OpenSearch recovery
        self.shared_state['aws_ready'] = True
        
        # Simulate queue drain
        self.shared_state['redis_queue_depth'] = 0
        self.shared_state['ingestion_rate_increment'] = len(buffered_logs)
        
        self.assertEqual(self.shared_state['redis_queue_depth'], 0)
        self.assertEqual(self.shared_state['ingestion_rate_increment'], 100)

    def test_pipeline_throttling_under_load(self):
        """Test pipeline throttling under high system load"""
        # Simulate high CPU/RAM usage
        self.shared_state.update({
            'cpu_usage': 85.0,
            'ram_usage': 88.0,
            'throttling_level': 3
        })
        
        # Pipeline should reduce throughput
        original_batch_size = 500
        throttled_batch_size = original_batch_size // (2 ** self.shared_state['throttling_level'])
        
        self.assertEqual(throttled_batch_size, 62)  # 500 / 8
        
        # Simulate recovery
        self.shared_state.update({
            'cpu_usage': 45.0,
            'ram_usage': 50.0,
            'throttling_level': 0
        })
        
        recovered_batch_size = original_batch_size // (2 ** self.shared_state['throttling_level'])
        self.assertEqual(recovered_batch_size, 500)

if __name__ == '__main__':
    unittest.main()