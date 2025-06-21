"""
Smart API Core Module

A universal API integration system with dynamic client generation,
flexible authentication, and standardized responses.
"""

from .registry import SmartAPIRegistry
from .client import SmartAPIClient
from .schema import APIResponse, ProviderConfig, EndpointConfig
from .response_adapter import ResponseAdapter

__all__ = [
    'SmartAPIRegistry',
    'SmartAPIClient', 
    'APIResponse',
    'ProviderConfig',
    'EndpointConfig',
    'ResponseAdapter'
] 