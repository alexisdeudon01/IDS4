#!/usr/bin/env python3
import unittest
import sys
import os

# Add modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'modules'))

# Import all test modules
from test_base_component import *
from test_config_manager import *
from test_connectivity_async import *
from test_docker_manager import *
from test_main import *
from test_metrics_server import *
from test_resource_controller import *
from test_aws_connectivity import *
from test_api_functionality import *
from test_aws_opensearch_domain import *
from test_pipeline_integration import *

if __name__ == '__main__':
    # Discover and run all tests
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(__file__)
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print test summary
    print(f"\n{'='*50}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success: {result.wasSuccessful()}")
    print(f"{'='*50}")
    
    # Exit with error code if tests failed
    sys.exit(0 if result.wasSuccessful() else 1)