"""
Smart API Clients

Pythonic API clients that provide method-based access to APIs.
Instead of client.call_endpoint('get_user'), use client.get_user().
"""

from .universal import UniversalAPIClient
from .github import GithubAPIClient
from .hubspot import HubspotAPIClient

__all__ = [
    'UniversalAPIClient',
    'GithubAPIClient',
    'HubspotAPIClient',
] 