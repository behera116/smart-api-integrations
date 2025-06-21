# Adding a New Provider to Smart API

This guide walks you through adding a new API provider to the Smart API system. The process is straightforward and typically takes 10-15 minutes.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Step-by-Step Guide](#step-by-step-guide)
3. [Provider Configuration](#provider-configuration)
4. [Authentication Setup](#authentication-setup)
5. [Endpoint Configuration](#endpoint-configuration)
6. [Creating a Client Class](#creating-a-client-class)
7. [Testing Your Provider](#testing-your-provider)
8. [Best Practices](#best-practices)

## Quick Start

The fastest way to add a new provider is using the `add_provider` command:

```bash
# Interactive mode (recommended for first-time setup)
python manage.py add_provider --interactive

# Or direct command with options
python manage.py add_provider \
  --name myapi \
  --base-url "https://api.myservice.com/v1" \
  --auth bearer \
  --create-client
```

This creates:
- `providers/myapi/config.yaml` - Provider configuration
- `clients/myapi.py` - Python client class (optional)

## Step-by-Step Guide

### 1. Create Provider Directory

```bash
mkdir -p newfies/smart_api/providers/myapi
```

### 2. Create Configuration File

Create `providers/myapi/config.yaml`:

```yaml
# Basic provider information
name: "myapi"
base_url: "https://api.myservice.com/v1"
description: "MyAPI integration for Smart API"
version: "1.0"

# Authentication configuration
auth:
  type: "bearer_token"  # Options: bearer_token, api_key, oauth2, basic, jwt, none
  token_value: "${MYAPI_TOKEN}"  # Environment variable

# Default headers for all requests
default_headers:
  "Accept": "application/json"
  "Content-Type": "application/json"
  "User-Agent": "Smart-API-Client/1.0"

# Timeout settings
default_timeout: 30.0

# Rate limiting (optional)
rate_limit:
  requests_per_second: 10
  requests_per_minute: 600

# Retry configuration
retry:
  max_retries: 3
  backoff_factor: 0.3
  retry_on_status: [429, 500, 502, 503, 504]

# Define your endpoints
endpoints:
  # ... endpoints go here (see section below)
```

### 3. Create Client Class (Optional but Recommended)

Create `clients/myapi.py`:

```python
"""
MyAPI client for Smart API integration.
"""

import os
from .universal import UniversalAPIClient


class MyAPIClient(UniversalAPIClient):
    """
    MyAPI client with automatic method generation.
    
    Usage:
        client = MyAPIClient()
        response = client.get_user()
        response = client.create_resource(json_data={'name': 'test'})
    """
    
    def __init__(self, token: str = None):
        """
        Initialize MyAPI client.
        
        Args:
            token: API token (defaults to MYAPI_TOKEN env var)
        """
        token = token or os.getenv('MYAPI_TOKEN')
        if not token:
            raise ValueError("MYAPI_TOKEN environment variable is required")
        
        super().__init__('myapi', token_value=token)
```

### 4. Update Client Imports

Add your client to `clients/__init__.py`:

```python
from .myapi import MyAPIClient

__all__ = [
    # ... existing clients
    'MyAPIClient',
]
```

## Provider Configuration

### Basic Configuration

```yaml
name: "myapi"                    # Provider identifier (lowercase, no spaces)
base_url: "https://api.example.com/v1"  # API base URL
description: "Provider description"      # Human-readable description
version: "1.0"                          # API version
```

### Advanced Configuration

```yaml
# Custom timeout per endpoint
default_timeout: 30.0

# Global rate limiting
rate_limit:
  requests_per_second: 10
  burst_limit: 20

# Custom retry strategy
retry:
  max_retries: 3
  backoff_factor: 0.5
  retry_on_status: [429, 500, 502, 503, 504]
  retry_on_exception: ["ConnectionError", "Timeout"]

# Environment-specific settings
environments:
  production:
    base_url: "https://api.example.com/v1"
  staging:
    base_url: "https://staging-api.example.com/v1"
```

## Authentication Setup

### Bearer Token

```yaml
auth:
  type: "bearer_token"
  token_value: "${MYAPI_TOKEN}"
  token_prefix: "Bearer"  # Optional, defaults to "Bearer"
```

### API Key

```yaml
auth:
  type: "api_key"
  api_key_header: "X-API-Key"  # Header name
  api_key_value: "${MYAPI_API_KEY}"
```

### OAuth2 Client Credentials

```yaml
auth:
  type: "oauth2"
  oauth2_client_id: "${MYAPI_CLIENT_ID}"
  oauth2_client_secret: "${MYAPI_CLIENT_SECRET}"
  oauth2_token_url: "https://api.example.com/oauth/token"
  oauth2_scopes: ["read", "write"]
  cache_tokens: true  # Cache tokens until expiry
```

### Basic Authentication

```yaml
auth:
  type: "basic"
  username: "${MYAPI_USERNAME}"
  password: "${MYAPI_PASSWORD}"
```

### JWT Token

```yaml
auth:
  type: "jwt"
  jwt_token: "${MYAPI_JWT_TOKEN}"
  jwt_algorithm: "HS256"  # or RS256, ES256, etc.
```

### Custom Authentication

```yaml
auth:
  type: "custom"
  custom_headers:
    "X-Custom-Auth": "${MYAPI_CUSTOM_TOKEN}"
    "X-Client-ID": "${MYAPI_CLIENT_ID}"
```

## Endpoint Configuration

### Basic Endpoint

```yaml
endpoints:
  get_user:
    path: "/user"
    method: "GET"
    description: "Get current user information"
```

### Endpoint with Path Parameters

```yaml
endpoints:
  get_user_by_id:
    path: "/users/{user_id}"
    method: "GET"
    description: "Get user by ID"
    parameters:
      user_id:
        type: "string"
        required: true
        in: "path"
        description: "User identifier"
```

### Endpoint with Query Parameters

```yaml
endpoints:
  list_users:
    path: "/users"
    method: "GET"
    description: "List all users"
    parameters:
      page:
        type: "integer"
        required: false
        in: "query"
        description: "Page number"
        default: 1
      per_page:
        type: "integer"
        required: false
        in: "query"
        description: "Results per page"
        default: 20
      status:
        type: "string"
        required: false
        in: "query"
        description: "Filter by status"
        enum: ["active", "inactive", "pending"]
```

### Endpoint with Body Parameters

```yaml
endpoints:
  create_user:
    path: "/users"
    method: "POST"
    description: "Create a new user"
    parameters:
      email:
        type: "string"
        required: true
        in: "body"
        description: "User email address"
      name:
        type: "string"
        required: true
        in: "body"
        description: "User full name"
      role:
        type: "string"
        required: false
        in: "body"
        description: "User role"
        default: "user"
        enum: ["admin", "user", "guest"]
```

### Complex Endpoint Example

```yaml
endpoints:
  search_resources:
    path: "/resources/search"
    method: "POST"
    description: "Search resources with filters"
    headers:  # Endpoint-specific headers
      "X-Search-Version": "2.0"
    parameters:
      query:
        type: "string"
        required: true
        in: "body"
        description: "Search query"
      filters:
        type: "object"
        required: false
        in: "body"
        description: "Search filters"
        properties:
          category:
            type: "string"
            description: "Resource category"
          date_from:
            type: "string"
            format: "date"
            description: "Start date (ISO 8601)"
          date_to:
            type: "string"
            format: "date"
            description: "End date (ISO 8601)"
      pagination:
        type: "object"
        required: false
        in: "body"
        properties:
          page:
            type: "integer"
            default: 1
          limit:
            type: "integer"
            default: 50
            maximum: 100
    rate_limit:  # Endpoint-specific rate limit
      requests_per_minute: 10
    timeout: 60.0  # Endpoint-specific timeout
```

## Testing Your Provider

### 1. Set Environment Variables

```bash
export MYAPI_TOKEN="your-api-token-here"
```

### 2. Test Basic Connection

```python
from newfies.smart_api.clients import MyAPIClient

# Initialize client
client = MyAPIClient()

# Test a simple endpoint
response = client.get_user()
print(f"Status: {response.status_code}")
print(f"Data: {response.data}")
```

### 3. Generate Type Stubs

```bash
python manage.py generate_type_stubs --provider myapi
```

This creates `typings/myapi.pyi` for IDE autocomplete.

### 4. Test with Management Command

```bash
# List available endpoints
python manage.py list_endpoints --provider myapi

# Test specific endpoint
python manage.py test_endpoint --provider myapi --endpoint get_user
```

### 5. Run Integration Tests

Create `tests/test_myapi.py`:

```python
import pytest
from newfies.smart_api.clients import MyAPIClient


class TestMyAPIIntegration:
    @pytest.fixture
    def client(self):
        return MyAPIClient()
    
    def test_get_user(self, client):
        response = client.get_user()
        assert response.success
        assert response.status_code == 200
        assert 'id' in response.data
    
    def test_list_resources(self, client):
        response = client.list_resources(params={'per_page': 10})
        assert response.success
        assert len(response.data) <= 10
    
    def test_create_resource(self, client):
        response = client.create_resource(json_data={
            'name': 'Test Resource',
            'description': 'Created by test'
        })
        assert response.success
        assert response.status_code == 201
```

## Best Practices

### 1. Use Environment Variables

Always use environment variables for sensitive data:

```yaml
auth:
  type: "bearer_token"
  token_value: "${MYAPI_TOKEN}"  # Good
  # token_value: "sk_live_abc123"  # Bad - never hardcode secrets
```

### 2. Document Parameters

Provide clear descriptions for all parameters:

```yaml
parameters:
  user_id:
    type: "string"
    required: true
    in: "path"
    description: "Unique user identifier (UUID format)"
    pattern: "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
```

### 3. Handle Pagination

Standardize pagination parameters:

```yaml
parameters:
  page:
    type: "integer"
    required: false
    in: "query"
    description: "Page number (1-based)"
    default: 1
    minimum: 1
  per_page:
    type: "integer"
    required: false
    in: "query"
    description: "Results per page"
    default: 20
    minimum: 1
    maximum: 100
```

### 4. Version Your API

Include version in configuration:

```yaml
name: "myapi"
base_url: "https://api.example.com/v2"  # Version in URL
version: "2.0"  # Configuration version

# Or use headers for versioning
default_headers:
  "API-Version": "2023-01-01"
```

### 5. Error Handling

The Smart API system automatically handles errors, but you can customize:

```yaml
endpoints:
  risky_operation:
    path: "/risky"
    method: "POST"
    description: "Operation that might fail"
    retry:
      max_retries: 5  # More retries for critical operations
      backoff_factor: 1.0  # Longer backoff
    timeout: 120.0  # Longer timeout
```

### 6. Use Consistent Naming

Follow naming conventions:

```yaml
endpoints:
  # Good: verb_noun format
  get_user: ...
  list_users: ...
  create_user: ...
  update_user: ...
  delete_user: ...
  
  # Avoid: inconsistent naming
  user: ...
  users_list: ...
  newUser: ...
```

## Common Patterns

### RESTful CRUD Operations

```yaml
endpoints:
  # List resources
  list_resources:
    path: "/resources"
    method: "GET"
    description: "List all resources"
    
  # Get single resource
  get_resource:
    path: "/resources/{id}"
    method: "GET"
    description: "Get resource by ID"
    parameters:
      id:
        type: "string"
        required: true
        in: "path"
        
  # Create resource
  create_resource:
    path: "/resources"
    method: "POST"
    description: "Create new resource"
    
  # Update resource
  update_resource:
    path: "/resources/{id}"
    method: "PUT"
    description: "Update resource"
    parameters:
      id:
        type: "string"
        required: true
        in: "path"
        
  # Delete resource
  delete_resource:
    path: "/resources/{id}"
    method: "DELETE"
    description: "Delete resource"
    parameters:
      id:
        type: "string"
        required: true
        in: "path"
```

### Search Endpoints

```yaml
endpoints:
  search:
    path: "/search"
    method: "POST"  # POST for complex queries
    description: "Search with advanced filters"
    parameters:
      q:
        type: "string"
        required: true
        in: "body"
        description: "Search query"
      filters:
        type: "object"
        required: false
        in: "body"
        description: "Advanced filters"
```

### Bulk Operations

```yaml
endpoints:
  bulk_create:
    path: "/resources/bulk"
    method: "POST"
    description: "Create multiple resources"
    parameters:
      resources:
        type: "array"
        required: true
        in: "body"
        description: "Array of resources to create"
    timeout: 120.0  # Longer timeout for bulk operations
```

## Troubleshooting

### Provider Not Found

```bash
# Check if provider is registered
python manage.py list_providers

# Verify configuration file exists
ls newfies/smart_api/providers/myapi/config.yaml
```

### Authentication Errors

```bash
# Check environment variables
echo $MYAPI_TOKEN

# Test with explicit token
python -c "
from newfies.smart_api.clients import MyAPIClient
client = MyAPIClient(token='your-token-here')
response = client.get_user()
print(response.error if not response.success else 'Success')
"
```

### Endpoint Not Found

```bash
# List all endpoints for provider
python manage.py list_endpoints --provider myapi

# Check endpoint configuration
grep -A 5 "endpoint_name:" providers/myapi/config.yaml
```

## Next Steps

1. **Add Webhook Support**: See [Adding a New Webhook](adding_new_webhook.md)
2. **Generate Documentation**: Use `python manage.py generate_provider_docs --provider myapi`
3. **Share Your Provider**: Submit a PR to share your provider configuration with the community

For more examples, check the existing providers in `providers/` directory. 