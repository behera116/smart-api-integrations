"""
Tests for GitHub provider endpoints.

This test file verifies that all GitHub provider endpoints work correctly.
It requires a valid GitHub token set in the GITHUB_TOKEN environment variable.

Run with: pytest -xvs tests/test_github_provider.py
"""

import os
import pytest
from typing import Dict, Any

# Add project root to path if needed
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the client
from src.core.registry import get_client

# Skip all tests if no GitHub token is available
pytestmark = pytest.mark.skipif(
    'GITHUB_TOKEN' not in os.environ,
    reason="GITHUB_TOKEN environment variable not set"
)

# Set providers directory
os.environ['SMART_API_INTEGRATIONS_PROVIDERS_DIR'] = str(Path(__file__).parent.parent / 'providers')


@pytest.fixture
def github_client():
    """Fixture to provide a GitHub client for tests."""
    return get_client('github')


def test_get_user(github_client):
    """Test the get_user endpoint."""
    response = github_client.call_endpoint('get_user')
    
    assert response.success is True
    assert response.status_code == 200
    assert 'login' in response.data
    assert 'id' in response.data
    
    print(f"Authenticated as: {response.data['login']}")


def test_list_repos(github_client):
    """Test the list_repos endpoint."""
    response = github_client.call_endpoint('list_repos', params={'per_page': 5})
    
    assert response.success is True
    assert response.status_code == 200
    assert isinstance(response.data, list)
    
    if len(response.data) > 0:
        repo = response.data[0]
        assert 'name' in repo
        assert 'id' in repo
        
        print(f"Found repositories: {[r['name'] for r in response.data[:5]]}")


def test_endpoint_3(github_client):
    """Test the endpoint_3 (get authenticated user) endpoint."""
    # This appears to be a duplicate of get_user but with different parameter expectations
    response = github_client.call_endpoint('endpoint_3', headers={'authorization': f"token {os.environ['GITHUB_TOKEN']}"})
    
    assert response.success is True
    assert response.status_code == 200
    assert 'login' in response.data
    assert 'id' in response.data


def test_endpoint_4(github_client):
    """Test the endpoint_4 (update authenticated user) endpoint."""
    # This is a PATCH request to update user data
    # We'll just test it with the current values to avoid changing the user profile
    
    # First get current user data
    user_response = github_client.call_endpoint('get_user')
    assert user_response.success is True
    
    # Now update with the same data (no actual change)
    current_data = {
        'name': user_response.data.get('name'),
        'email': user_response.data.get('email'),
        'bio': user_response.data.get('bio')
    }
    
    # Remove None values to avoid setting fields to null
    update_data = {k: v for k, v in current_data.items() if v is not None}
    
    if update_data:  # Only test if we have data to update
        response = github_client.call_endpoint(
            'endpoint_4',
            headers={'authorization': f"token {os.environ['GITHUB_TOKEN']}"},
            json_data=update_data
        )
        
        assert response.success is True
        assert response.status_code == 200
        
        # Verify the response contains the same data we sent
        for key, value in update_data.items():
            if value is not None:
                assert response.data.get(key) == value


def test_endpoint_5(github_client):
    """Test the endpoint_5 (get user by ID) endpoint."""
    # First get authenticated user to get an ID
    user_response = github_client.call_endpoint('get_user')
    assert user_response.success is True
    
    user_id = user_response.data.get('id')
    assert user_id is not None
    
    # Now get user by ID
    response = github_client.call_endpoint(
        'endpoint_5',
        headers={'authorization': f"token {os.environ['GITHUB_TOKEN']}"},
        params={'account_id': user_id}
    )
    
    assert response.success is True
    assert response.status_code == 200
    assert response.data.get('id') == user_id


def test_endpoint_6(github_client):
    """Test the endpoint_6 (list followers) endpoint."""
    response = github_client.call_endpoint(
        'endpoint_6',
        params={'per_page': 5}
    )
    
    assert response.success is True
    assert response.status_code == 200
    assert isinstance(response.data, list)
    
    print(f"Found {len(response.data)} followers")
    
    if len(response.data) > 0:
        follower = response.data[0]
        assert 'login' in follower
        assert 'id' in follower


def test_endpoint_7(github_client):
    """Test the endpoint_7 (list following) endpoint."""
    response = github_client.call_endpoint(
        'endpoint_7',
        params={'per_page': 5}
    )
    
    assert response.success is True
    assert response.status_code == 200
    assert isinstance(response.data, list)
    
    print(f"Following {len(response.data)} users")
    
    if len(response.data) > 0:
        following = response.data[0]
        assert 'login' in following
        assert 'id' in following


def test_endpoint_8(github_client):
    """Test the endpoint_8 (check if following user) endpoint."""
    # First get a list of users the authenticated user is following
    following_response = github_client.call_endpoint('endpoint_7')
    assert following_response.success is True
    
    if len(following_response.data) > 0:
        # Get the first user being followed
        username = following_response.data[0]['login']
        
        # Check if following that user
        response = github_client.call_endpoint(
            'endpoint_8',
            headers={'authorization': f"token {os.environ['GITHUB_TOKEN']}"},
            params={'username': username}
        )
        
        # GitHub returns 204 No Content if following, 404 if not following
        assert response.status_code in [204, 404]
        
        if response.status_code == 204:
            print(f"Confirmed following user: {username}")
        else:
            print(f"Not following user: {username}")
    else:
        pytest.skip("User is not following anyone, skipping test_endpoint_8")


def test_all_endpoints_have_tests():
    """Verify that all GitHub endpoints have corresponding tests."""
    # Get the client to inspect available endpoints
    client = get_client('github')
    
    # Get all endpoint names
    endpoint_names = set(client.config.endpoints.keys())
    
    # Get all test functions that test endpoints
    test_functions = [
        name for name in globals()
        if name.startswith('test_') and callable(globals()[name])
    ]
    
    # Check that each endpoint has a test
    for endpoint in endpoint_names:
        test_name = f"test_{endpoint}"
        assert test_name in test_functions, f"Missing test for endpoint: {endpoint}"
        
    print(f"All {len(endpoint_names)} endpoints have tests") 