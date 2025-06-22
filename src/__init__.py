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
OPENAI_AVAILABLE = importlib.util.find_spec("openai") is not None

def check_dependencies():
    """Return a dictionary of available optional dependencies"""
    return {
        "django": DJANGO_AVAILABLE,
        "flask": FLASK_AVAILABLE,
        "fastapi": FASTAPI_AVAILABLE,
        "openai": OPENAI_AVAILABLE
    }

# CLI entry point function
def cli():
    """Entry point for the command-line interface."""
    from .cli.main import main
    import sys
    sys.exit(main())

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
    'cli',
    'DJANGO_AVAILABLE',
    'FLASK_AVAILABLE',
    'FASTAPI_AVAILABLE',
    'OPENAI_AVAILABLE'
] 