# 🛡️ Type Safety & IDE Support Guide

## 🎯 Overview

Smart API Integrations provides comprehensive type safety and IDE support through generated type stubs, intelligent parameter validation, and runtime type checking. Get full autocomplete, error detection, and documentation right in your IDE.

## ✨ Key Benefits

- **Full IDE Autocomplete**: Method names, parameters, and return types
- **Compile-time Error Detection**: Catch errors before runtime
- **Parameter Validation**: Automatic validation of required/optional parameters
- **Documentation Integration**: Inline documentation and examples
- **Type Hints**: Complete type annotations for all generated code

## 🚀 Quick Start

### 1. Generate Type Stubs

```bash
# Generate type stubs for a provider
smart-api-integrations generate-type-stubs github --output-dir ./typings

# Generate for multiple providers
smart-api-integrations generate-type-stubs stripe --output-dir ./typings
smart-api-integrations generate-type-stubs myapi --output-dir ./typings
```

### 2. Configure Your IDE

Add the typings directory to your Python path:

**VS Code (`settings.json`):**
```json
{
    "python.analysis.extraPaths": ["./typings"],
    "python.analysis.typeCheckingMode": "basic"
}
```

**PyCharm:**
1. Go to File → Settings → Project → Python Interpreter
2. Click the gear icon → Show All → Show paths for the selected interpreter
3. Add `./typings` to the path

### 3. Enjoy Full IDE Support

```python
from smart_api_integrations import GithubAPIClient

github = GithubAPIClient()

# IDE shows all available methods with documentation
user = github.get_user(username='octocat')  # Full autocomplete!
#             ^^^^^^^^ IDE suggests parameter names

# Type checking catches errors
user = github.get_user()  # Error: missing required parameter 'username'
repos = github.list_repos(per_page='invalid')  # Error: per_page should be int
```

## 🏗️ Generated Type Stubs

### Basic Type Stub Structure

```python
# typings/github.pyi
from typing import Optional
from smart_api_integrations.core.schema import APIResponse

class GithubAPIClient:
    def __init__(self, **auth_overrides) -> None: ...
    
    def get_user(self, username: str) -> APIResponse:
        """
        Get a user by username.
        
        Args:
            username: The username to lookup
            
        Returns:
            APIResponse containing user data
        """
        ...
    
    def list_repos(
        self, 
        username: Optional[str] = None,
        per_page: Optional[int] = None,
        page: Optional[int] = None
    ) -> APIResponse:
        """
        List repositories for a user.
        
        Args:
            username: Username to list repos for
            per_page: Number of results per page (1-100)
            page: Page number for pagination
            
        Returns:
            APIResponse containing repository list
        """
        ...
```

### Advanced Type Annotations

```python
# typings/stripe.pyi
from typing import Optional, Dict, Any, List
from smart_api_integrations.core.schema import APIResponse

class StripeAPIClient:
    def create_customer(
        self,
        email: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> APIResponse:
        """
        Create a new customer.
        
        Args:
            email: Customer's email address (required)
            name: Customer's full name
            description: Arbitrary string for your use
            metadata: Set of key-value pairs for custom data
            
        Returns:
            APIResponse containing created customer object
            
        Example:
            customer = stripe.create_customer(
                email="john@example.com",
                name="John Doe",
                metadata={"user_id": "123"}
            )
        """
        ...
    
    def list_customers(
        self,
        limit: Optional[int] = None,
        starting_after: Optional[str] = None,
        ending_before: Optional[str] = None,
        email: Optional[str] = None
    ) -> APIResponse:
        """List customers with optional filtering."""
        ...
```

## 🔍 Parameter Validation

### Automatic Validation

Smart API Integrations automatically validates parameters based on your endpoint configuration:

```python
# This configuration enables automatic validation
# providers/myapi/config.yaml
endpoints:
  create_user:
    path: /users
    method: POST
    parameters:
      email:
        type: string
        required: true
        in: body
        format: email
      age:
        type: integer
        required: false
        in: body
        minimum: 0
        maximum: 150
```

```python
# Runtime validation based on configuration
client = UniversalAPIClient('myapi')

# This will raise a validation error
try:
    client.create_user(age=200)  # age > maximum
except ValueError as e:
    print(f"Validation error: {e}")

# This will raise a validation error for missing required parameter
try:
    client.create_user(age=25)  # missing required 'email'
except ValueError as e:
    print(f"Missing required parameter: {e}")
```

### Custom Validation

```python
from smart_api_integrations import UniversalAPIClient
from typing import Dict, Any

class ValidatedAPIClient(UniversalAPIClient):
    def __init__(self, provider_name: str, **auth_overrides):
        super().__init__(provider_name, **auth_overrides)
    
    def _validate_email(self, email: str) -> bool:
        """Custom email validation."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def create_user(self, email: str, **kwargs) -> 'APIResponse':
        """Create user with email validation."""
        if not self._validate_email(email):
            raise ValueError(f"Invalid email format: {email}")
        
        return super().create_user(email=email, **kwargs)
```

## 🎭 IDE Integration Features

### Method Discovery

```python
# IDE shows all available methods
client = UniversalAPIClient('github')
client.  # IDE shows: get_user, list_repos, create_repo, etc.

# Get help for specific methods
help_text = client.get_method_help('get_user')
print(help_text)
# Output:
# GET /users/{username} - Get a user by username
# Parameters:
#   - username (string, in path) (required): The username to lookup
# Usage: client.get_user(username='...')
```

### Parameter Hints

```python
# IDE shows parameter hints and types
github.get_user(
    username='octocat'  # IDE shows: (required) str - The username to lookup
)

github.list_repos(
    username='octocat',  # (optional) str - Username to list repos for
    per_page=30,         # (optional) int - Number of results per page (1-100)
    page=1               # (optional) int - Page number for pagination
)
```

### Error Detection

```python
# IDE catches these errors before runtime:

# Missing required parameter
github.get_user()  # Error: Missing required argument 'username'

# Wrong parameter type
github.list_repos(per_page='30')  # Error: Expected int, got str

# Unknown parameter
github.get_user(username='octocat', invalid_param=True)  # Warning: Unexpected keyword argument

# Typo in method name
github.get_usr('octocat')  # Error: 'GithubAPIClient' has no attribute 'get_usr'
```

## 📚 Documentation Integration

### Inline Documentation

```python
# Hover over methods to see documentation
github.get_user(username='octocat')
#      ^^^^^^^^ IDE shows:
# Get a user by username.
# 
# Args:
#     username: The username to lookup
# 
# Returns:
#     APIResponse containing user data
# 
# Example:
#     user = github.get_user(username='octocat')
#     print(user.data['name'])
```

### Response Type Information

```python
from smart_api_integrations.core.schema import APIResponse

response: APIResponse = github.get_user(username='octocat')

# IDE knows the structure of APIResponse
if response.success:
    data = response.data        # Dict[str, Any]
    status = response.status_code  # int
    headers = response.headers     # Dict[str, str]
else:
    error = response.error         # str
    status = response.status_code  # int
```

## 🔧 Advanced Type Features

### Generic Type Support

```python
from typing import TypeVar, Generic
from smart_api_integrations.core.schema import APIResponse

T = TypeVar('T')

class TypedAPIResponse(APIResponse, Generic[T]):
    """Type-safe API response."""
    data: T

# Usage with custom types
from dataclasses import dataclass

@dataclass
class User:
    id: str
    name: str
    email: str

def get_typed_user(username: str) -> TypedAPIResponse[User]:
    """Get user with typed response."""
    response = github.get_user(username=username)
    if response.success:
        user_data = User(**response.data)
        return TypedAPIResponse(
            success=True,
            data=user_data,
            status_code=response.status_code,
            headers=response.headers
        )
    return response
```

### Protocol-Based Typing

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class APIClientProtocol(Protocol):
    """Protocol for API clients."""
    
    def get_user(self, username: str) -> APIResponse: ...
    def list_repos(self, username: str) -> APIResponse: ...

def process_github_data(client: APIClientProtocol) -> None:
    """Function that works with any GitHub-compatible client."""
    user = client.get_user(username='octocat')
    repos = client.list_repos(username='octocat')
    # Process data...

# Works with any client that implements the protocol
github_client = GithubAPIClient()
process_github_data(github_client)  # Type checker approves
```

## 🧪 Testing with Type Safety

### Type-Safe Test Fixtures

```python
# tests/conftest.py
import pytest
from typing import Dict, Any
from smart_api_integrations import GithubAPIClient
from smart_api_integrations.core.schema import APIResponse

@pytest.fixture
def mock_user_response() -> APIResponse:
    """Type-safe mock response."""
    return APIResponse(
        success=True,
        data={
            'id': 1,
            'login': 'octocat',
            'name': 'The Octocat',
            'email': 'octocat@github.com'
        },
        status_code=200,
        headers={'content-type': 'application/json'}
    )

@pytest.fixture
def github_client() -> GithubAPIClient:
    """Type-safe client fixture."""
    return GithubAPIClient(token_value='fake-token-for-testing')
```

### Type-Safe Mock Responses

```python
# tests/test_github.py
from unittest.mock import Mock, patch
from smart_api_integrations import GithubAPIClient

def test_get_user_with_types():
    """Test with full type safety."""
    client = GithubAPIClient(token_value='fake-token')
    
    # Mock with proper typing
    mock_response = Mock(spec=APIResponse)
    mock_response.success = True
    mock_response.data = {'login': 'octocat', 'name': 'The Octocat'}
    mock_response.status_code = 200
    
    with patch.object(client, 'get_user', return_value=mock_response):
        result = client.get_user(username='octocat')
        
        # Type checker knows these attributes exist
        assert result.success
        assert result.data['login'] == 'octocat'
        assert result.status_code == 200
```

## 🚀 Best Practices

### 1. Always Generate Type Stubs

```bash
# Generate stubs for all your providers
smart-api-integrations generate-type-stubs github
smart-api-integrations generate-type-stubs stripe
smart-api-integrations generate-type-stubs myapi
```

### 2. Use Type Hints in Your Code

```python
from smart_api_integrations import GithubAPIClient
from smart_api_integrations.core.schema import APIResponse

def process_user_data(client: GithubAPIClient, username: str) -> dict:
    """Process user data with type hints."""
    response: APIResponse = client.get_user(username=username)
    
    if response.success:
        return {
            'user_id': response.data['id'],
            'username': response.data['login'],
            'name': response.data.get('name', 'Unknown')
        }
    
    raise ValueError(f"Failed to get user: {response.error}")
```

### 3. Validate Parameters Early

```python
def create_user_safe(client: UniversalAPIClient, email: str, age: int) -> APIResponse:
    """Create user with early validation."""
    # Validate before API call
    if not email or '@' not in email:
        raise ValueError("Invalid email address")
    
    if age < 0 or age > 150:
        raise ValueError("Age must be between 0 and 150")
    
    return client.create_user(email=email, age=age)
```

### 4. Use IDE Features

- **Enable type checking** in your IDE settings
- **Install Python type checker** (mypy, pylance, etc.)
- **Configure auto-import** for Smart API Integrations modules
- **Use code completion** extensively to discover available methods

## 🔍 Troubleshooting

### Type Stubs Not Working

```bash
# Regenerate type stubs
smart-api-integrations generate-type-stubs myapi --output-dir ./typings

# Check IDE configuration
# Make sure ./typings is in your Python path
```

### Missing Method Suggestions

```python
# Check if provider is configured correctly
client = UniversalAPIClient('myapi')
methods = client.list_available_methods()
print(methods)  # Should show all available methods
```

### Parameter Validation Errors

```python
# Check endpoint configuration
smart-api-integrations info myapi --show-endpoints
smart-api-integrations validate --provider myapi
```

## 📚 Next Steps

- **[API Client Guide](api-client-guide.md)** - Learn more about using API clients
- **[CLI Reference](cli-reference.md)** - Generate type stubs and more
- **[Examples](examples/README.md)** - See type safety in real examples
- **[Best Practices](best-practices.md)** - Production-ready patterns 