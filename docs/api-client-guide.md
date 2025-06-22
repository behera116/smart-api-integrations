# 🔌 API Client Guide

## 🎯 Overview

Smart API Integrations transforms API integration from repetitive boilerplate to intelligent, type-safe client classes. Define endpoints once in YAML, get powerful clients with full IDE support.

## 🚀 Core Benefits

### ❌ Before: Traditional API Integration
```python
import requests

def get_github_user(username):
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    response = requests.get(f'https://api.github.com/users/{username}', headers=headers)
    if response.status_code != 200:
        raise Exception(f"API error: {response.status_code}")
    return response.json()

def get_github_repo(owner, repo):
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    response = requests.get(f'https://api.github.com/repos/{owner}/{repo}', headers=headers)
    if response.status_code != 200:
        raise Exception(f"API error: {response.status_code}")
    return response.json()

# Repeat for every endpoint...
```

### ✅ After: Smart API Integration
```python
from smart_api_integrations import GithubAPIClient

github = GithubAPIClient()  # Uses GITHUB_TOKEN automatically
user = github.get_user(username='octocat')           # Full IDE support!
repo = github.get_repo(owner='octocat', repo='Hello-World')
```

## 🔧 Client Types

### 1. Universal Client
Works with any configured provider:

```python
from smart_api_integrations import UniversalAPIClient

# Initialize for any provider
client = UniversalAPIClient('github')
user = client.get_user(username='octocat')

# Switch providers easily
stripe = UniversalAPIClient('stripe')
customers = stripe.list_customers(limit=10)
```

### 2. Provider-Specific Clients
Pre-built clients with provider-specific optimizations:

```python
from smart_api_integrations import GithubAPIClient, StripeAPIClient

github = GithubAPIClient()    # Uses GITHUB_TOKEN
stripe = StripeAPIClient()    # Uses STRIPE_API_KEY
```

### 3. Custom Client Classes
Extend with your business logic:

```python
from smart_api_integrations import UniversalAPIClient

class MyAPIClient(UniversalAPIClient):
    def __init__(self, **auth_overrides):
        # Auto-detect authentication from environment
        if 'token_value' not in auth_overrides:
            token = os.getenv('MYAPI_TOKEN')
            if token:
                auth_overrides['token_value'] = token
        
        super().__init__('myapi', **auth_overrides)
    
    def get_active_users(self):
        """Custom business logic method."""
        users = self.list_users()
        if users.success:
            return [u for u in users.data if u.get('status') == 'active']
        return []
```

## 🧠 Intelligent Parameter Handling

The system automatically routes parameters based on your endpoint configuration:

```python
# Path parameters (go in URL)
user = api.get_user(user_id='123')  # → GET /users/123

# Query parameters (go in URL query string)  
users = api.list_users(page=2, limit=50)  # → GET /users?page=2&limit=50

# Body parameters (go in JSON body)
new_user = api.create_user(name='John', email='john@example.com')
# → POST /users with body: {"name": "John", "email": "john@example.com"}

# Mixed parameters (automatically separated)
result = api.update_user(
    user_id='123',        # → path parameter
    name='John Smith',    # → body parameter
    notify=True          # → query parameter
)
# → PUT /users/123?notify=true with body: {"name": "John Smith"}
```

## 🔐 Authentication

### Automatic Environment Variable Detection
```python
# Each provider uses its own environment variables
github = GithubAPIClient()        # Uses GITHUB_TOKEN
stripe = StripeAPIClient()        # Uses STRIPE_API_KEY
salesforce = SalesforceAPIClient() # Uses SALESFORCE_CLIENT_ID + SALESFORCE_CLIENT_SECRET
```

### Authentication Override
```python
# Override any authentication parameter
github = GithubAPIClient(token_value='custom_token')
stripe = StripeAPIClient(api_key_value='sk_test_custom')
salesforce = SalesforceAPIClient(
    oauth2_client_id='custom_id',
    oauth2_client_secret='custom_secret'
)
```

### Supported Authentication Types

| Auth Type | Environment Variables | Override Parameters |
|-----------|----------------------|-------------------|
| Bearer Token | `{PROVIDER}_TOKEN` | `token_value` |
| API Key | `{PROVIDER}_API_KEY` | `api_key_value` |
| Basic Auth | `{PROVIDER}_USERNAME`, `{PROVIDER}_PASSWORD` | `username`, `password` |
| OAuth2 | `{PROVIDER}_CLIENT_ID`, `{PROVIDER}_CLIENT_SECRET` | `oauth2_client_id`, `oauth2_client_secret` |
| JWT | `{PROVIDER}_JWT_TOKEN` | `jwt_token` |

## 📊 Response Handling

All API calls return standardized `APIResponse` objects:

```python
response = client.get_user(user_id='123')

# Check success
if response.success:
    user_data = response.data
    print(f"User: {user_data['name']}")
else:
    print(f"Error: {response.error}")
    print(f"Status: {response.status_code}")

# Access raw response
print(f"Headers: {response.headers}")
print(f"Status: {response.status_code}")
```

## 🎯 Real-World Examples

### Stripe Integration
```python
from smart_api_integrations import UniversalAPIClient

class StripeClient(UniversalAPIClient):
    def __init__(self):
        super().__init__('stripe')
    
    def find_customer_by_email(self, email: str):
        """Find customer by email address."""
        customers = self.list_customers()
        if customers.success:
            for customer in customers.data['data']:
                if customer.get('email') == email:
                    return customer
        return None
    
    def create_customer_safe(self, email: str, name: str = None):
        """Create customer only if email doesn't exist."""
        existing = self.find_customer_by_email(email)
        if existing:
            return {'exists': True, 'customer': existing}
        
        result = self.create_customer(email=email, name=name)
        return {'exists': False, 'customer': result.data if result.success else None}

# Usage
stripe = StripeClient()
safe_result = stripe.create_customer_safe('jane@example.com', 'Jane Doe')
```

### Multi-Provider Data Sync
```python
class DataSyncService:
    def __init__(self):
        self.github = GithubAPIClient()
        self.slack = UniversalAPIClient('slack')
        self.hubspot = UniversalAPIClient('hubspot')
    
    def sync_user_activity(self, user_id: str):
        # Get GitHub activity
        github_user = self.github.get_user(username=user_id)
        
        # Post to Slack
        if github_user.success:
            message = f"GitHub activity for {github_user.data['name']}"
            self.slack.post_message(channel='#dev', text=message)
        
        # Update CRM
        self.hubspot.update_contact(
            contact_id=user_id,
            properties={'last_github_activity': datetime.now().isoformat()}
        )
```

## 🔍 Method Discovery

### List Available Methods
```python
client = UniversalAPIClient('github')

# Get all available methods
methods = client.list_available_methods()
for method_name, description in methods.items():
    print(f"{method_name}: {description}")
```

### Get Method Help
```python
# Get detailed help for a specific method
help_text = client.get_method_help('get_user')
print(help_text)
# Output:
# GET /users/{username} - Get a user by username
# Parameters:
#   - username (string, in path) (required): The username to lookup
# Usage: client.get_user(params={...})
```

## 🛠️ Advanced Usage

### Raw API Calls
```python
# Make raw API calls when needed
response = client.call_raw('GET', '/custom/endpoint', params={'key': 'value'})
```

### Context Management
```python
# Use with context managers for automatic cleanup
with UniversalAPIClient('myapi') as client:
    users = client.list_users()
    # Client automatically closed
```

### Error Handling
```python
try:
    user = client.get_user(user_id='invalid')
    if not user.success:
        if user.status_code == 404:
            print("User not found")
        elif user.status_code == 401:
            print("Authentication failed")
        else:
            print(f"API error: {user.error}")
except Exception as e:
    print(f"Network error: {e}")
```

## 🚀 Next Steps

- **[Generate type stubs](type-safety-guide.md)** for full IDE support
- **[Add new providers](adding-new-providers.md)** for your APIs
- **[Learn about authentication](authentication-guide.md)** options
- **[See real examples](examples/README.md)** with complete code 