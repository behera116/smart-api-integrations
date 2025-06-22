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
    
    def __init__(self, **auth_overrides):
        """
        Initialize GitHub API client.
        
        Args:
            **auth_overrides: Authentication overrides (e.g., token_value='your_token')
                            If not provided, reads from GITHUB_TOKEN environment variable
        """
        # Set default token from environment if not provided
        if 'token_value' not in auth_overrides:
            github_token = os.getenv('GITHUB_TOKEN')
            if github_token:
                auth_overrides['token_value'] = github_token
            else:
                raise ValueError("GitHub token required. Set GITHUB_TOKEN environment variable or pass token_value.")
        
        super().__init__('github', **auth_overrides) 