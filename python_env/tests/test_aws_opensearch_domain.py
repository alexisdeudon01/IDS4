import unittest
import multiprocessing
import sys
import os
import json
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError

# Add modules to path
modules_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'modules'))
if modules_path not in sys.path:
    sys.path.insert(0, modules_path)

from aws_manager import AWSManager
from config_manager import ConfigManager

class TestAWSOpenSearchDomain(unittest.TestCase):
    """Test AWS OpenSearch domain operations"""
    
    def setUp(self):
        self.manager = multiprocessing.Manager()
        self.shared_state = self.manager.dict({
            'aws_ready': False,
            'last_error': ''
        })
        
        self.config_manager = Mock(spec=ConfigManager)
        self.config_manager.get.side_effect = lambda key, default=None: {
            'aws.region': 'eu-central-1',
            'aws.domain_name': 'test-suricata-domain',
            'aws.opensearch_endpoint': '',
            'aws.access_key_id': 'test_key',
            'aws.secret_access_key': 'test_secret'
        }.get(key, default)

    @patch('boto3.Session')
    def test_provision_domain_already_active(self, mock_session):
        """Test domain provisioning when domain is already active"""
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
    def test_provision_domain_processing_then_active(self, mock_session):
        """Test domain provisioning when domain is processing then becomes active"""
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance
        mock_opensearch_client = Mock()
        mock_session_instance.client.return_value = mock_opensearch_client
        
        # First call: processing, second call: active
        mock_opensearch_client.describe_domain.side_effect = [
            {
                'DomainStatus': {
                    'ProcessingState': 'Processing',
                    'Endpoint': 'https://test-domain.eu-central-1.es.amazonaws.com'
                }
            },
            {
                'DomainStatus': {
                    'ProcessingState': 'Active',
                    'Endpoint': 'https://test-domain.eu-central-1.es.amazonaws.com'
                }
            }
        ]
        
        aws_manager = AWSManager(self.shared_state, self.config_manager)
        
        with patch('time.sleep'):
            result = aws_manager.provision_opensearch_domain(max_wait_time=60)
        
        self.assertTrue(result)
        self.assertTrue(self.shared_state['aws_ready'])

    @patch('boto3.Session')
    def test_provision_domain_timeout(self, mock_session):
        """Test domain provisioning timeout"""
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance
        mock_opensearch_client = Mock()
        mock_session_instance.client.return_value = mock_opensearch_client
        
        mock_opensearch_client.describe_domain.return_value = {
            'DomainStatus': {
                'ProcessingState': 'Processing',
                'Endpoint': 'https://test-domain.eu-central-1.es.amazonaws.com'
            }
        }
        
        aws_manager = AWSManager(self.shared_state, self.config_manager)
        
        with patch('time.sleep'), patch('time.time', side_effect=[0, 61]):
            result = aws_manager.provision_opensearch_domain(max_wait_time=60)
        
        self.assertFalse(result)
        self.assertFalse(self.shared_state['aws_ready'])

    @patch('boto3.Session')
    def test_provision_domain_not_found_create_success(self, mock_session):
        """Test domain creation when domain doesn't exist"""
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance
        mock_opensearch_client = Mock()
        mock_sts_client = Mock()
        
        mock_session_instance.client.side_effect = lambda service, **kwargs: {
            'opensearch': mock_opensearch_client,
            'sts': mock_sts_client
        }[service]
        
        # First call: not found, second call: active after creation
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
        
        # Verify create_domain was called with correct parameters
        call_args = mock_opensearch_client.create_domain.call_args[1]
        self.assertEqual(call_args['DomainName'], 'test-suricata-domain')
        self.assertTrue(call_args['NodeToNodeEncryptionOptions']['Enabled'])
        self.assertTrue(call_args['EncryptionAtRestOptions']['Enabled'])

    @patch('boto3.Session')
    def test_provision_domain_create_failure(self, mock_session):
        """Test domain creation failure"""
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance
        mock_opensearch_client = Mock()
        mock_sts_client = Mock()
        
        mock_session_instance.client.side_effect = lambda service, **kwargs: {
            'opensearch': mock_opensearch_client,
            'sts': mock_sts_client
        }[service]
        
        mock_opensearch_client.describe_domain.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException'}}, 'DescribeDomain'
        )
        mock_sts_client.get_caller_identity.return_value = {'Account': '123456789012'}
        mock_opensearch_client.create_domain.side_effect = ClientError(
            {'Error': {'Code': 'ValidationException', 'Message': 'Invalid domain name'}}, 
            'CreateDomain'
        )
        
        aws_manager = AWSManager(self.shared_state, self.config_manager)
        result = aws_manager.provision_opensearch_domain()
        
        self.assertFalse(result)
        self.assertFalse(self.shared_state['aws_ready'])

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
        aws_manager.opensearch_endpoint = 'https://test-domain.eu-central-1.es.amazonaws.com'
        
        result = aws_manager.apply_index_template()
        
        self.assertTrue(result)
        mock_opensearch_instance.indices.put_index_template.assert_called_once()
        
        # Verify template structure
        call_args = mock_opensearch_instance.indices.put_index_template.call_args[1]
        template_body = call_args['body']
        self.assertIn('index_patterns', template_body)
        self.assertEqual(template_body['index_patterns'], ['suricata-*'])
        self.assertIn('template', template_body)
        self.assertIn('mappings', template_body['template'])

    @patch('opensearchpy.OpenSearch')
    @patch('boto3.Session')
    def test_apply_index_template_failure(self, mock_session, mock_opensearch):
        """Test index template application failure"""
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance
        mock_credentials = Mock()
        mock_credentials.access_key = 'test_access'
        mock_credentials.secret_key = 'test_secret'
        mock_credentials.token = None
        mock_session_instance.get_credentials.return_value = mock_credentials
        
        mock_opensearch_instance = Mock()
        mock_opensearch.return_value = mock_opensearch_instance
        mock_opensearch_instance.indices.put_index_template.return_value = {'acknowledged': False}
        
        aws_manager = AWSManager(self.shared_state, self.config_manager)
        aws_manager.opensearch_endpoint = 'https://test-domain.eu-central-1.es.amazonaws.com'
        
        result = aws_manager.apply_index_template()
        
        self.assertFalse(result)

    @patch('opensearchpy.OpenSearch')
    @patch('boto3.Session')
    def test_apply_index_template_no_client(self, mock_session, mock_opensearch):
        """Test index template application with no OpenSearch client"""
        aws_manager = AWSManager(self.shared_state, self.config_manager)
        aws_manager.opensearch_endpoint = None
        
        result = aws_manager.apply_index_template()
        
        self.assertFalse(result)

    @patch('boto3.Session')
    def test_domain_with_service_software_options(self, mock_session):
        """Test domain status with ServiceSoftwareOptions"""
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance
        mock_opensearch_client = Mock()
        mock_session_instance.client.return_value = mock_opensearch_client
        
        mock_opensearch_client.describe_domain.return_value = {
            'DomainStatus': {
                'ServiceSoftwareOptions': {'UpdateStatus': 'Completed'},
                'Endpoint': 'https://test-domain.eu-central-1.es.amazonaws.com'
            }
        }
        
        aws_manager = AWSManager(self.shared_state, self.config_manager)
        result = aws_manager.provision_opensearch_domain()
        
        self.assertTrue(result)
        self.assertTrue(self.shared_state['aws_ready'])

    @patch('boto3.Session')
    def test_domain_access_policy_creation(self, mock_session):
        """Test domain creation with proper access policies"""
        mock_session_instance = Mock()
        mock_session.return_value = mock_session_instance
        mock_opensearch_client = Mock()
        mock_sts_client = Mock()
        
        mock_session_instance.client.side_effect = lambda service, **kwargs: {
            'opensearch': mock_opensearch_client,
            'sts': mock_sts_client
        }[service]
        
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
        aws_manager.provision_opensearch_domain()
        
        # Verify access policy structure
        call_args = mock_opensearch_client.create_domain.call_args[1]
        access_policies = json.loads(call_args['AccessPolicies'])
        
        self.assertEqual(access_policies['Version'], '2012-10-17')
        self.assertEqual(len(access_policies['Statement']), 1)
        statement = access_policies['Statement'][0]
        self.assertEqual(statement['Effect'], 'Allow')
        self.assertEqual(statement['Action'], 'es:*')
        self.assertIn('123456789012', statement['Principal']['AWS'])

if __name__ == '__main__':
    unittest.main()