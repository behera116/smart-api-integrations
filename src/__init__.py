"""
Smart API Integrations

A smart way to integrate 3rd party APIs and Webhooks with minimal effort.
"""

# Import core components for easy access
from .core import SmartAPIClient, SmartAPIRegistry, APIResponse, ProviderConfig, EndpointConfig, ResponseAdapter
from .clients import UniversalAPIClient, GithubAPIClient, HubspotAPIClient

# Check for optional dependencies
import importlib.util

DJANGO_AVAILABLE = importlib.util.find_spec("django") is not None
FLASK_AVAILABLE = importlib.util.find_spec("flask") is not None
FASTAPI_AVAILABLE = importlib.util.find_spec("fastapi") is not None

def check_dependencies():
    """Return a dictionary of available optional dependencies"""
    return {
        "django": DJANGO_AVAILABLE,
        "flask": FLASK_AVAILABLE,
        "fastapi": FASTAPI_AVAILABLE
    }

__version__ = "0.1.0"

__all__ = [
    'SmartAPIClient',
    'SmartAPIRegistry',
    'APIResponse',
    'ProviderConfig',
    'EndpointConfig',
    'ResponseAdapter',
    'UniversalAPIClient',
    'GithubAPIClient',
    'HubspotAPIClient',
    'check_dependencies',
    'DJANGO_AVAILABLE',
    'FLASK_AVAILABLE',
    'FASTAPI_AVAILABLE'
] 