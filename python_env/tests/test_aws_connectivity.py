import unittest
import asyncio
import multiprocessing
import sys
import os
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import json
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'modules'))

from aws_manager import AWSManager
from connectivity_async import ConnectivityAsync
from config_manager import ConfigManager

class TestAWSConnectivity(unittest.TestCase):
    
    def setUp(self):
        self.manager = multiprocessing.Manager()
        self.shared_state = self.manager.dict({
            'aws_ready': False,
            'redis_ready': False,
            'pipeline_ok': False,
            'last_error': ''
        })
        self.shutdown_event = multiprocessing.Event()
        
        # Mock config
        self.config_manager = Mock(spec=ConfigManager)
        self.config_manager.get.side_effect = lambda key, default=None: {
            'aws.region': 'eu-central-1',
            'aws.opensearch_endpoint': 'https://test-domain.eu-central-1.es.amazonaws.com',
            'aws.domain_name': 'test-domain',
            'aws.access_key_id': 'test_key',
            'aws.secret_access_key': 'test_secret',
            'redis.host': 'localhost',
            'redis.port': 6379,
            'connectivity.max_retries': 3,
            'connectivity.initial_backoff': 1,
            'connectivity.check_interval': 5
        }.get(key, default)

    @patch('boto3.Session')
    def test_aws_manager_init_success(self, mock_session):
        """Test successful AWSManager initialization"""
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance
        
        aws_manager = AWSManager(self.shared_state, self.config_manager)
        
        self.assertEqual(aws_manager.aws_region, 'eu-central-1')
        self.assertEqual(aws_manager.opensearch_endpoint, 'https://test-domain.eu-central-1.es.amazonaws.com')
        mock_session.assert_called_once()

    @patch('boto3.Session')
    def test_aws_manager_init_no_region(self, mock_session):
        """Test AWSManager initialization fails without region"""
        self.config_manager.get.side_effect = lambda key, default=None: {
            'aws.region': None,
            'aws.opensearch_endpoint': 'https://test-domain.eu-central-1.es.amazonaws.com',
            'aws.domain_name': 'test-domain'
        }.get(key, default)
        
        with self.assertRaises(ValueError):
            AWSManager(self.shared_state, self.config_manager)

    @patch('boto3.Session')
    def test_get_aws_session_with_credentials(self, mock_session):
        """Test AWS session creation with explicit credentials"""
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance
        
        aws_manager = AWSManager(self.shared_state, self.config_manager)
        
        mock_session.assert_called_with(
            aws_access_key_id='test_key',
            aws_secret_access_key='test_secret',
            region_name='eu-central-1'
        )

    @patch('boto3.Session')
    def test_get_aws_session_no_credentials_error(self, mock_session):
        """Test AWS session creation fails with no credentials"""
        mock_session.side_effect = NoCredentialsError()
        
        with self.assertRaises(NoCredentialsError):
            AWSManager(self.shared_state, self.config_manager)

    @patch('opensearchpy.OpenSearch')
    @patch('boto3.Session')
    def test_get_opensearch_client_success(self, mock_session, mock_opensearch):
        """Test successful OpenSearch client creation"""
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance
        mock_credentials = Mock()
        mock_credentials.access_key = 'test_access'
        mock_credentials.secret_key = 'test_secret'
        mock_credentials.token = None
        mock_session_instance.get_credentials.return_value = mock_credentials
        
        mock_opensearch_instance = Mock()
        mock_opensearch.return_value = mock_opensearch_instance
        
        aws_manager = AWSManager(self.shared_state, self.config_manager)
        client = aws_manager._get_opensearch_client()
        
        self.assertIsNotNone(client)
        mock_opensearch.assert_called_once()

    @patch('boto3.Session')
    def test_get_opensearch_client_no_endpoint(self, mock_session):
        """Test OpenSearch client creation fails without endpoint"""
        self.config_manager.get.side_effect = lambda key, default=None: {
            'aws.region': 'eu-central-1',
            'aws.opensearch_endpoint': None,
            'aws.domain_name': 'test-domain'
        }.get(key, default)
        
        aws_manager = AWSManager(self.shared_state, self.config_manager)
        client = aws_manager._get_opensearch_client()
        
        self.assertIsNone(client)

    @patch('opensearchpy.OpenSearch')
    @patch('boto3.Session')
    def test_send_bulk_to_opensearch_success(self, mock_session, mock_opensearch):
        """Test successful bulk send to OpenSearch"""
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance
        mock_credentials = Mock()
        mock_credentials.access_key = 'test_access'
        mock_credentials.secret_key = 'test_secret'
        mock_credentials.token = None
        mock_session_instance.get_credentials.return_value = mock_credentials
        
        mock_opensearch_instance = Mock()
        mock_opensearch.return_value = mock_opensearch_instance
        mock_opensearch_instance.bulk.return_value = {'errors': False}
        
        aws_manager = AWSManager(self.shared_state, self.config_manager)
        
        test_logs = [
            {'@timestamp': '2024-01-01T10:00:00Z', 'message': 'test log 1'},
            {'@timestamp': '2024-01-01T10:00:01Z', 'message': 'test log 2'}
        ]
        
        result = aws_manager.send_bulk_to_opensearch(test_logs)
        
        self.assertTrue(result)
        self.assertTrue(self.shared_state['aws_ready'])
        mock_opensearch_instance.bulk.assert_called_once()

    @patch('opensearchpy.OpenSearch')
    @patch('boto3.Session')
    def test_send_bulk_to_opensearch_failure(self, mock_session, mock_opensearch):
        """Test bulk send to OpenSearch failure"""
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance
        mock_credentials = Mock()
        mock_credentials.access_key = 'test_access'
        mock_credentials.secret_key = 'test_secret'
        mock_credentials.token = None
        mock_session_instance.get_credentials.return_value = mock_credentials
        
        mock_opensearch_instance = Mock()
        mock_opensearch.return_value = mock_opensearch_instance
        mock_opensearch_instance.bulk.return_value = {'errors': True, 'items': []}
        
        aws_manager = AWSManager(self.shared_state, self.config_manager)
        
        test_logs = [{'@timestamp': '2024-01-01T10:00:00Z', 'message': 'test log'}]
        result = aws_manager.send_bulk_to_opensearch(test_logs)
        
        self.assertFalse(result)
        self.assertFalse(self.shared_state['aws_ready'])

    @patch('boto3.Session')
    def test_provision_opensearch_domain_exists(self, mock_session):
        """Test OpenSearch domain provisioning when domain exists"""
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance
        mock_opensearch_client = Mock()
        mock_session_instance.client.return_value = mock_opensearch_client
        
        mock_opensearch_client.describe_domain.return_value = {
            'DomainStatus': {
                'ProcessingState': 'Active',
                'Endpoint': 'https://test-domain.eu-central-1.es.amazonaws.com'
            }
        }
        
        aws_manager = AWSManager(self.shared_state, self.config_manager)
        result = aws_manager.provision_opensearch_domain()
        
        self.assertTrue(result)
        self.assertTrue(self.shared_state['aws_ready'])
        self.assertEqual(aws_manager.opensearch_endpoint, 'https://test-domain.eu-central-1.es.amazonaws.com')

    @patch('boto3.Session')
    def test_provision_opensearch_domain_not_found(self, mock_session):
        """Test OpenSearch domain provisioning when domain doesn't exist"""
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance
        mock_opensearch_client = Mock()
        mock_sts_client = Mock()
        mock_session_instance.client.side_effect = lambda service, **kwargs: {
            'opensearch': mock_opensearch_client,
            'sts': mock_sts_client
        }[service]
        
        # First call raises ResourceNotFoundException, second call returns active domain
        mock_opensearch_client.describe_domain.side_effect = [
            ClientError({'Error': {'Code': 'ResourceNotFoundException'}}, 'DescribeDomain'),
            {
                'DomainStatus': {
                    'ProcessingState': 'Active',
                    'Endpoint': 'https://test-domain.eu-central-1.es.amazonaws.com'
                }
            }
        ]
        
        mock_sts_client.get_caller_identity.return_value = {'Account': '123456789012'}
        mock_opensearch_client.create_domain.return_value = {}
        
        aws_manager = AWSManager(self.shared_state, self.config_manager)
        result = aws_manager.provision_opensearch_domain()
        
        self.assertTrue(result)
        mock_opensearch_client.create_domain.assert_called_once()

    @patch('opensearchpy.OpenSearch')
    @patch('boto3.Session')
    def test_apply_index_template_success(self, mock_session, mock_opensearch):
        """Test successful index template application"""
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance
        mock_credentials = Mock()
        mock_credentials.access_key = 'test_access'
        mock_credentials.secret_key = 'test_secret'
        mock_credentials.token = None
        mock_session_instance.get_credentials.return_value = mock_credentials
        
        mock_opensearch_instance = Mock()
        mock_opensearch.return_value = mock_opensearch_instance
        mock_opensearch_instance.indices.put_index_template.return_value = {'acknowledged': True}
        
        aws_manager = AWSManager(self.shared_state, self.config_manager)
        result = aws_manager.apply_index_template()
        
        self.assertTrue(result)
        mock_opensearch_instance.indices.put_index_template.assert_called_once()

class TestConnectivityAsyncAWS(unittest.TestCase):
    
    def setUp(self):
        self.manager = multiprocessing.Manager()
        self.shared_state = self.manager.dict({
            'aws_ready': False,
            'redis_ready': False,
            'pipeline_ok': False,
            'last_error': ''
        })
        self.shutdown_event = multiprocessing.Event()
        
        # Mock config
        self.config_manager = Mock(spec=ConfigManager)
        self.config_manager.get.side_effect = lambda key, default=None: {
            'aws.region': 'eu-central-1',
            'aws.opensearch_endpoint': 'https://test-domain.eu-central-1.es.amazonaws.com',
            'aws.domain_name': 'test-domain',
            'redis.host': 'localhost',
            'redis.port': 6379,
            'connectivity.max_retries': 3,
            'connectivity.initial_backoff': 1,
            'connectivity.check_interval': 5
        }.get(key, default)

    @patch('modules.connectivity_async.AWSManager')
    def test_connectivity_async_init(self, mock_aws_manager):
        """Test ConnectivityAsync initialization"""
        connectivity = ConnectivityAsync(self.shared_state, self.config_manager, self.shutdown_event)
        
        self.assertEqual(connectivity.opensearch_endpoint, 'https://test-domain.eu-central-1.es.amazonaws.com')
        self.assertEqual(connectivity.aws_region, 'eu-central-1')
        mock_aws_manager.assert_called_once()

    @patch('modules.connectivity_async.AWSManager')
    async def test_check_dns_resolution_success(self, mock_aws_manager):
        """Test successful DNS resolution"""
        connectivity = ConnectivityAsync(self.shared_state, self.config_manager, self.shutdown_event)
        
        with patch('asyncio.get_event_loop') as mock_loop:
            mock_loop.return_value.getaddrinfo = AsyncMock(return_value=[])
            result = await connectivity.check_dns_resolution('test-domain.eu-central-1.es.amazonaws.com')
            self.assertTrue(result)

    @patch('modules.connectivity_async.AWSManager')
    async def test_check_dns_resolution_failure(self, mock_aws_manager):
        """Test DNS resolution failure"""
        import socket
        connectivity = ConnectivityAsync(self.shared_state, self.config_manager, self.shutdown_event)
        
        with patch('asyncio.get_event_loop') as mock_loop:
            mock_loop.return_value.getaddrinfo = AsyncMock(side_effect=socket.gaierror("DNS resolution failed"))
            
            with self.assertRaises(socket.gaierror):
                await connectivity.check_dns_resolution('invalid-domain.com')

    @patch('modules.connectivity_async.AWSManager')
    async def test_check_tls_handshake_success(self, mock_aws_manager):
        """Test successful TLS handshake"""
        connectivity = ConnectivityAsync(self.shared_state, self.config_manager, self.shutdown_event)
        
        mock_writer = Mock()
        mock_writer.close = Mock()
        mock_writer.wait_closed = AsyncMock()
        
        with patch('asyncio.open_connection', new_callable=AsyncMock) as mock_open_connection:
            mock_open_connection.return_value = (Mock(), mock_writer)
            result = await connectivity.check_tls_handshake('test-domain.eu-central-1.es.amazonaws.com')
            self.assertTrue(result)

    @patch('modules.connectivity_async.AWSManager')
    async def test_check_opensearch_bulk_test_success(self, mock_aws_manager):
        """Test successful OpenSearch bulk test"""
        mock_aws_manager_instance = Mock()
        mock_aws_manager.return_value = mock_aws_manager_instance
        
        mock_client = Mock()
        mock_client.cluster.health.return_value = {'status': 'green'}
        mock_aws_manager_instance._get_opensearch_client.return_value = mock_client
        
        connectivity = ConnectivityAsync(self.shared_state, self.config_manager, self.shutdown_event)
        
        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = {'status': 'green'}
            result = await connectivity.check_opensearch_bulk_test()
            
            self.assertTrue(result)
            self.assertTrue(self.shared_state['aws_ready'])

    @patch('modules.connectivity_async.AWSManager')
    async def test_check_opensearch_bulk_test_no_endpoint(self, mock_aws_manager):
        """Test OpenSearch bulk test with no endpoint"""
        connectivity = ConnectivityAsync(self.shared_state, self.config_manager, self.shutdown_event)
        connectivity.opensearch_endpoint = None
        
        result = await connectivity.check_opensearch_bulk_test()
        
        self.assertFalse(result)
        self.assertFalse(self.shared_state['aws_ready'])

    @patch('modules.connectivity_async.AWSManager')
    async def test_check_redis_connectivity_success(self, mock_aws_manager):
        """Test successful Redis connectivity"""
        connectivity = ConnectivityAsync(self.shared_state, self.config_manager, self.shutdown_event)
        
        mock_writer = Mock()
        mock_writer.close = Mock()
        mock_writer.wait_closed = AsyncMock()
        
        with patch('asyncio.open_connection', new_callable=AsyncMock) as mock_open_connection:
            mock_open_connection.return_value = (Mock(), mock_writer)
            result = await connectivity.check_redis_connectivity()
            
            self.assertTrue(result)
            self.assertTrue(self.shared_state['redis_ready'])

    @patch('modules.connectivity_async.AWSManager')
    async def test_retry_operation_success(self, mock_aws_manager):
        """Test retry operation success on first attempt"""
        connectivity = ConnectivityAsync(self.shared_state, self.config_manager, self.shutdown_event)
        
        async def mock_func():
            return True
        
        result = await connectivity._retry_operation(mock_func)
        self.assertTrue(result)

    @patch('modules.connectivity_async.AWSManager')
    async def test_retry_operation_failure_then_success(self, mock_aws_manager):
        """Test retry operation failure then success"""
        connectivity = ConnectivityAsync(self.shared_state, self.config_manager, self.shutdown_event)
        
        call_count = 0
        async def mock_func():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("First attempt fails")
            return True
        
        with patch('asyncio.sleep', new_callable=AsyncMock):
            result = await connectivity._retry_operation(mock_func)
            self.assertTrue(result)
            self.assertEqual(call_count, 2)

    @patch('modules.connectivity_async.AWSManager')
    async def test_retry_operation_max_retries_exceeded(self, mock_aws_manager):
        """Test retry operation exceeds max retries"""
        connectivity = ConnectivityAsync(self.shared_state, self.config_manager, self.shutdown_event)
        
        async def mock_func():
            raise Exception("Always fails")
        
        with patch('asyncio.sleep', new_callable=AsyncMock):
            with self.assertRaises(Exception):
                await connectivity._retry_operation(mock_func)

if __name__ == '__main__':
    unittest.main()