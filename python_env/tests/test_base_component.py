import unittest
import multiprocessing
import sys
import os
from unittest.mock import Mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'modules'))

from base_component import BaseComponent
from config_manager import ConfigManager

class TestBaseComponent(unittest.TestCase):
    
    def setUp(self):
        self.manager = multiprocessing.Manager()
        self.shared_state = self.manager.dict()
        self.config_manager = Mock(spec=ConfigManager)
        self.shutdown_event = multiprocessing.Event()
        
    def test_initialization(self):
        component = BaseComponent(self.shared_state, self.config_manager, self.shutdown_event)
        self.assertIsNotNone(component.logger)
        self.assertEqual(component.shared_state, self.shared_state)
        
    def test_get_config(self):
        self.config_manager.get.return_value = "test_value"
        component = BaseComponent(self.shared_state, self.config_manager, self.shutdown_event)
        result = component.get_config("test.key", "default")
        self.assertEqual(result, "test_value")
        
    def test_update_shared_state(self):
        component = BaseComponent(self.shared_state, self.config_manager, self.shutdown_event)
        component.update_shared_state("test_key", "test_value")
        self.assertEqual(self.shared_state["test_key"], "test_value")

if __name__ == '__main__':
    unittest.main()