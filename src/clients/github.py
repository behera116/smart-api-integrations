"""
GitHub API Client - Simple alias for method-based access.
"""

import os
from .universal import UniversalAPIClient


class GithubAPIClient(UniversalAPIClient):
    """
    GitHub API Client.
    
    Usage:
        github = GithubAPIClient()  # Gets token from GITHUB_TOKEN env var
        user = github.get_user()
        repos = github.list_repos(per_page=10)
    """
    
    # Optional method mapping - maps Python method names to actual endpoints
    METHOD_MAPPING = {
        'list_repos': 'list_user_repos',
        'get_profile': 'get_user',
        'my_repos': 'list_user_repos',
    }
    
    def __init__(self, token_value: str = None):
        """
        Initialize GitHub API client.
        
        Args:
            token_value: GitHub token (optional, defaults to GITHUB_TOKEN env var)
        """
        token = token_value or os.getenv('GITHUB_TOKEN')
        if not token:
            raise ValueError("GitHub token required. Set GITHUB_TOKEN environment variable or pass token_value.")
        
        super().__init__('github', token_value=token) 