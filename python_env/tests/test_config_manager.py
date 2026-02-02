import unittest
import tempfile
import os
import yaml
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'modules'))

from config_manager import ConfigManager

class TestConfigManager(unittest.TestCase):
    
    def setUp(self):
        self.test_config = {
            'raspberry_pi': {
                'ip': '192.168.178.66',
                'cpu_limit_percent': 70
            },
            'prometheus': {
                'port': 9100
            }
        }
        
    def test_load_config(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(self.test_config, f)
            config_path = f.name
            
        try:
            config_manager = ConfigManager(config_path)
            self.assertEqual(config_manager.get('raspberry_pi.ip'), '192.168.178.66')
            self.assertEqual(config_manager.get('prometheus.port'), 9100)
        finally:
            os.unlink(config_path)
            
    def test_get_with_default(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(self.test_config, f)
            config_path = f.name
            
        try:
            config_manager = ConfigManager(config_path)
            self.assertEqual(config_manager.get('nonexistent.key', 'default'), 'default')
        finally:
            os.unlink(config_path)

if __name__ == '__main__':
    unittest.main()