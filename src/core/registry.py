"""
Registry for Smart API clients.
Manages client instances and provides a central access point.
Synchronous implementation for simplicity.
"""

from typing import Dict, Any, Optional
from .client import SmartAPIClient
from .loader import ConfigLoader


class SmartAPIRegistry:
    """Registry for Smart API clients."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SmartAPIRegistry, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._clients = {}
        self._config_loader = ConfigLoader()
        self._initialized = True
    
    def get_client(self, provider_name: str, **auth_overrides) -> SmartAPIClient:
        """Get a client for the specified provider."""
        # Create a cache key based on provider and auth overrides
        cache_key = provider_name
        if auth_overrides:
            # Sort keys for consistent cache key
            sorted_overrides = sorted(auth_overrides.items())
            cache_key = f"{provider_name}:{sorted_overrides}"
        
        # Return cached client if available
        if cache_key in self._clients:
            return self._clients[cache_key]
        
        # Load provider config
        config = self._config_loader.load_provider_config(provider_name)
        
        # Apply auth overrides
        if auth_overrides:
            self._apply_auth_overrides(config, auth_overrides)
        
        # Create client
        client = SmartAPIClient(config)
        
        # Cache client
        self._clients[cache_key] = client
        
        return client
    
    def list_providers(self) -> list:
        """List all available providers."""
        return self._config_loader.list_available_providers()
    
    def get_provider_info(self, provider_name: str) -> Dict[str, Any]:
        """Get information about a provider."""
        config = self._config_loader.load_provider_config(provider_name)
        return {
            'name': config.name,
            'base_url': config.base_url,
            'description': config.description,
            'version': config.version,
            'auth_type': config.auth.type.value if config.auth else 'none',
            'endpoint_count': len(config.endpoints) if config.endpoints else 0,
            'endpoints': list(config.endpoints.keys()) if config.endpoints else []
        }
    
    def _apply_auth_overrides(self, config, auth_overrides):
        """Apply authentication overrides to config."""
        if not config.auth:
            return
        
        for key, value in auth_overrides.items():
            if hasattr(config.auth, key):
                setattr(config.auth, key, value)


# Singleton instance
_registry = SmartAPIRegistry()

def get_client(provider_name: str, **auth_overrides) -> SmartAPIClient:
    """Get a client for the specified provider."""
    return _registry.get_client(provider_name, **auth_overrides)

def list_providers() -> list:
    """List all available providers."""
    return _registry.list_providers()

def get_provider_info(provider_name: str) -> Dict[str, Any]:
    """Get information about a provider."""
    return _registry.get_provider_info(provider_name) 