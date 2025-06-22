"""
Webhook registry for managing webhook processors and configurations.
"""

import os
import yaml
import logging
from typing import Dict, Optional
from pathlib import Path

from .webhook_schema import WebhookConfig, WebhookProviderConfig, WebhookVerificationType
from .webhook import WebhookProcessor

logger = logging.getLogger(__name__)


class WebhookRegistry:
    """Singleton registry for webhook processors."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.processors: Dict[str, WebhookProcessor] = {}
            self.provider_configs: Dict[str, WebhookProviderConfig] = {}
            self._load_configurations()
            WebhookRegistry._initialized = True
    
    def _load_configurations(self):
        """Load webhook configurations from YAML files."""
        try:
            # Get the src directory
            current_dir = Path(__file__).parent.parent
            providers_dir = current_dir / 'providers'
            
            if not providers_dir.exists():
                logger.info("No providers directory found, skipping webhook config loading")
                return
            
            # Load configurations from each provider directory
            for provider_dir in providers_dir.iterdir():
                if provider_dir.is_dir():
                    webhook_config_path = provider_dir / 'webhook.yaml'
                    if webhook_config_path.exists():
                        self._load_provider_config(provider_dir.name, webhook_config_path)
                        
        except Exception as e:
            logger.error(f"Failed to load webhook configurations: {e}")
    
    def _load_provider_config(self, provider_name: str, config_path: Path):
        """Load webhook configuration for a specific provider."""
        try:
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            webhooks_data = config_data.get('webhooks', {})
            webhooks = {}
            
            for webhook_name, webhook_data in webhooks_data.items():
                webhook_config = WebhookConfig(
                    path=webhook_data.get('path', f'/webhooks/{provider_name}/'),
                    verify_signature=webhook_data.get('verify_signature', True),
                    signing_secret_env=webhook_data.get('signing_secret_env'),
                    verification_type=WebhookVerificationType(
                        webhook_data.get('verification_type', 'hmac_sha256')
                    ),
                    signature_header=webhook_data.get('signature_header', 'X-Signature'),
                    timestamp_header=webhook_data.get('timestamp_header'),
                    replay_tolerance=webhook_data.get('replay_tolerance', 300),
                    events=webhook_data.get('events', []),
                    rate_limit=webhook_data.get('rate_limit')
                )
                webhooks[webhook_name] = webhook_config
            
            provider_config = WebhookProviderConfig(
                name=provider_name,
                webhooks=webhooks,
                default_verification_type=WebhookVerificationType(
                    config_data.get('default_verification_type', 'hmac_sha256')
                ),
                default_signature_header=config_data.get('default_signature_header', 'X-Signature'),
                default_timestamp_header=config_data.get('default_timestamp_header'),
                ip_whitelist=config_data.get('ip_whitelist')
            )
            
            self.provider_configs[provider_name] = provider_config
            logger.info(f"Loaded webhook config for provider: {provider_name}")
            
        except Exception as e:
            logger.error(f"Failed to load webhook config for {provider_name}: {e}")
    
    def get_processor(self, processor_key: str) -> Optional[WebhookProcessor]:
        """Get webhook processor by key (provider:webhook_name)."""
        return self.processors.get(processor_key)
    
    def create_processor(self, provider: str, webhook_name: str = 'default') -> WebhookProcessor:
        """Create a new webhook processor."""
        processor_key = f"{provider}:{webhook_name}"
        
        if processor_key in self.processors:
            return self.processors[processor_key]
        
        # Get provider config
        provider_config = self.provider_configs.get(provider)
        if not provider_config:
            raise ValueError(f"No webhook configuration found for provider: {provider}")
        
        # Get webhook config
        webhook_config = provider_config.get_webhook(webhook_name)
        if not webhook_config:
            raise ValueError(f"No webhook configuration found for {provider}:{webhook_name}")
        
        # Create processor
        processor = WebhookProcessor(provider, webhook_name, webhook_config)
        self.processors[processor_key] = processor
        
        logger.info(f"Created webhook processor: {processor_key}")
        return processor
    
    def register_processor(self, provider: str, webhook_name: str, processor: WebhookProcessor):
        """Register a custom webhook processor."""
        processor_key = f"{provider}:{webhook_name}"
        self.processors[processor_key] = processor
        logger.info(f"Registered custom webhook processor: {processor_key}")
    
    def list_providers(self) -> list:
        """List all available webhook providers."""
        return list(self.provider_configs.keys())
    
    def list_webhooks(self, provider: str) -> list:
        """List all webhooks for a provider."""
        provider_config = self.provider_configs.get(provider)
        if not provider_config:
            return []
        return list(provider_config.webhooks.keys())
    
    def get_provider_config(self, provider: str) -> Optional[WebhookProviderConfig]:
        """Get provider configuration."""
        return self.provider_configs.get(provider)


# Global registry instance
_registry = None


def get_webhook_registry() -> WebhookRegistry:
    """Get the global webhook registry instance."""
    global _registry
    if _registry is None:
        _registry = WebhookRegistry()
    return _registry


def reset_webhook_registry():
    """Reset the global registry (mainly for testing)."""
    global _registry
    _registry = None
    WebhookRegistry._instance = None
    WebhookRegistry._initialized = False 