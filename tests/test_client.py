"""
Tests for Smart API Client.
"""

import pytest
import os
from unittest.mock import Mock, patch

from smart_api_integrations import SmartAPIClient, check_dependencies


def test_check_dependencies():
    """Test dependency checking."""
    deps = check_dependencies()
    assert isinstance(deps, dict)
    assert 'django' in deps
    assert 'flask' in deps
    assert 'fastapi' in deps


def test_client_initialization():
    """Test client can be initialized."""
    with patch('smart_api_integrations.core.loader.ConfigLoader.load_provider_config') as mock_load:
        # Mock the config loading
        mock_load.return_value = Mock(
            name='test',
            base_url='https://api.test.com',
            auth=Mock(type='none'),
            endpoints={}
        )
        
        client = SmartAPIClient('test')
        assert client is not None
        assert hasattr(client, 'provider_name')


def test_environment_variable_resolution():
    """Test that environment variables are resolved in config."""
    os.environ['TEST_API_KEY'] = 'secret-key-123'
    
    with patch('smart_api_integrations.core.loader.ConfigLoader._load_yaml_config') as mock_load:
        # Test that ${TEST_API_KEY} gets resolved
        mock_config = {
            'base_url': 'https://api.test.com',
            'auth': {
                'type': 'api_key',
                'api_key_value': '${TEST_API_KEY}'
            }
        }
        
        from smart_api_integrations.core.loader import ConfigLoader
        loader = ConfigLoader()
        resolved = loader._resolve_env_vars(mock_config)
        
        assert resolved['auth']['api_key_value'] == 'secret-key-123'


def test_webhook_handler_decorator():
    """Test webhook handler decorator."""
    from smart_api_integrations.webhooks import webhook_handler
    
    @webhook_handler('test', 'test_event')
    def test_handler(event):
        return {'processed': True}
    
    # Verify the handler was registered
    from smart_api_integrations.core.webhook_registry import get_webhook_registry
    registry = get_webhook_registry()
    
    # The decorator should have registered the handler
    assert hasattr(test_handler, '__webhook_provider__')
    assert test_handler.__webhook_provider__ == 'test'
    assert test_handler.__webhook_event__ == 'test_event'


def test_framework_detection():
    """Test that framework detection works correctly."""
    from smart_api_integrations import DJANGO_AVAILABLE, FLASK_AVAILABLE, FASTAPI_AVAILABLE
    
    # These will be True/False based on what's installed
    assert isinstance(DJANGO_AVAILABLE, bool)
    assert isinstance(FLASK_AVAILABLE, bool)
    assert isinstance(FASTAPI_AVAILABLE, bool)
