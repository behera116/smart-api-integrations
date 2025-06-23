# 🚀 Smart API Integrations

**Connect to any API without writing boilerplate code. Turn API documentation into ready-to-use Python functions.**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 What This Package Does

Smart API Integrations makes it easy to use any API or receive webhook events (notifications from other services).

### Without This Package:
```python
# ❌ The old way: lots of repetitive code
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

# ... and so on for every endpoint
```

### With Smart API Integrations:
```python
# ✅ The better way: simple and clean
from smart_api_integrations import GithubAPIClient

github = GithubAPIClient()  # Uses GITHUB_TOKEN from environment variables
user = github.get_user(username='octocat')
repo = github.get_repo(owner='octocat', repo='Hello-World')
```

## 🚀 Quick Start

### 1. Install the Package

```bash
pip install smart-api-integrations
```

### 2. Set Environment Variables

```bash
# Where to find API configurations
export SMART_API_INTEGRATIONS_PROVIDERS_DIR="./providers"

# Your API tokens (examples for different services)
export GITHUB_TOKEN="your_github_token"
export STRIPE_API_KEY="sk_test_your_stripe_key"
```

### 3. Use Pre-built Providers

```python
from smart_api_integrations import GithubAPIClient

# Create a client that automatically uses your GITHUB_TOKEN
github = GithubAPIClient()

# Get information about a user
user = github.get_user(username='octocat')
print(f"User: {user.data['name']}")
```

## 🔧 Adding New API Providers

### Method 1: Using the CLI (Easiest)

The command-line tool can help you create a new provider:

```bash
# Create a new provider configuration
smart-api-integrations add-provider \
    --name "myapi" \
    --base-url "https://api.myservice.com/v1" \
    --auth-type "bearer_token"
```

### Method 2: Generate from OpenAPI Documentation

If your API has OpenAPI documentation (formerly known as Swagger), you can automatically generate a provider:

```bash
# Generate endpoints from API documentation
smart-api-integrations openapi-to-config \
    https://api.myservice.com/openapi.json \
    --output-dir "./providers" \
    --provider-name "myapi"
```

### Method 3: Manual Configuration

Create a YAML file with your API details:

```yaml
# providers/myapi/config.yaml
name: myapi
base_url: https://api.myservice.com/v1
description: My API Service
auth:
  type: bearer_token
  token_value: ${MYAPI_TOKEN}
endpoints:
  get_user:
    path: /users/{user_id}
    method: GET
    description: Get user by ID
    parameters:
      user_id: {type: string, required: true, in: path}
  list_users:
    path: /users
    method: GET
    description: List all users
    parameters:
      page: {type: integer, required: false, in: query}
      limit: {type: integer, required: false, in: query}
```

## 🎯 Using Your API Provider

### Option 1: Use the Universal Client (Easiest)

The universal client works with any provider you've configured:

```python
from smart_api_integrations import UniversalAPIClient

# Create a client for your API
myapi = UniversalAPIClient('myapi')  # Uses environment variables for auth

# Call API methods based on your config
user = myapi.get_user(user_id='123')
users = myapi.list_users(page=1, limit=10)
```

### Option 2: Generate a Dedicated Client Class

For better IDE support and type checking, you can generate a dedicated client class:

```bash
# Generate a client class file
smart-api-integrations generate-client myapi \
    --output-file "./my_project/myapi_client.py" \
    --class-name "MyAPIClient"
```

Then use the generated class:

```python
# Import your generated client
from my_project.myapi_client import MyAPIClient

# Create a client instance
client = MyAPIClient()  # Uses environment variables for auth

# Call methods with full IDE support
user = client.get_user(user_id='123')
```

### Option 3: Create a Custom Client Class

For advanced users who want to add custom business logic:

```python
from smart_api_integrations.clients.universal import UniversalAPIClient

class MyAPIClient(UniversalAPIClient):
    """Custom client with additional business logic."""
    
    def __init__(self):
        super().__init__('myapi')  # Use the 'myapi' provider
    
    def get_active_users(self):
        """Get only active users."""
        all_users = self.list_users()
        if all_users.success:
            return [user for user in all_users.data if user.get('status') == 'active']
        return []

# Usage
client = MyAPIClient()
active_users = client.get_active_users()
```

## 🛡️ Type Safety & IDE Support

### Generate Type Stubs

```bash
# Generate type stubs for full IDE support
smart-api-integrations generate-type-stubs myapi \
    --output-dir "./typings"
```

This creates `typings/myapi.pyi`:

```python
# Auto-generated type stubs
from smart_api_integrations.core.schema import APIResponse

class MyAPIClient:
    def get_user(self, user_id: str) -> APIResponse: ...
    def list_users(self, page: int = None, limit: int = None) -> APIResponse: ...
    def create_user(self, name: str, email: str) -> APIResponse: ...
```

### Using with Full IDE Support

```python
from smart_api_integrations import UniversalAPIClient

myapi = UniversalAPIClient('myapi')

# IDE will show:
# - Method suggestions: get_user, list_users, create_user
# - Parameter hints: user_id (required), page (optional), etc.
# - Return type: APIResponse
user = myapi.get_user(user_id='123')  # Full autocomplete!
```

## 🔧 Parameter Intelligence

The framework automatically handles different parameter types:

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

## 📖 Real-World Example: Stripe Integration

### 1. Create Configuration

```yaml
# providers/stripe/config.yaml
name: stripe
base_url: https://api.stripe.com/v1
auth:
  type: bearer_token
  token_value: ${STRIPE_API_KEY}
endpoints:
  list_customers:
    path: /customers
    method: GET
    parameters:
      limit: {type: integer, required: false, in: query}
  create_customer:
    path: /customers
    method: POST
    parameters:
      email: {type: string, required: true, in: body}
      name: {type: string, required: false, in: body}
  get_customer:
    path: /customers/{customer_id}
    method: GET
    parameters:
      customer_id: {type: string, required: true, in: path}
```

### 2. Generate Type Stubs

```bash
smart-api-integrations generate-type-stubs stripe
```

### 3. Create Custom Client

```python
# my_project/stripe_client.py
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
```

### 4. Use with Full IDE Support

```python
from my_project.stripe_client import StripeClient

stripe = StripeClient()

# Full autocomplete and type checking!
customers = stripe.list_customers(limit=10)
new_customer = stripe.create_customer(email='john@example.com', name='John Doe')
customer = stripe.get_customer(customer_id='cus_123')

# Custom methods
safe_result = stripe.create_customer_safe('jane@example.com', 'Jane Doe')
```

## 🔔 Receiving Webhooks (Events from Other Services)

Webhooks are how other services send notifications to your application (like when a payment is made or a GitHub repository is updated).

### Step 1: Configure a Webhook

Create a webhook configuration file:

```yaml
# providers/stripe/webhook.yaml
webhooks:
  default:
    path: /webhooks/stripe/
    verify_signature: true
    signing_secret_env: STRIPE_WEBHOOK_SECRET
```

### Step 2: Create Event Handlers

```python
from smart_api_integrations.webhooks import smart_webhook_handler

# Handle a specific event type
@smart_webhook_handler('stripe', 'payment_intent.succeeded')
def handle_payment_success(event):
    # This runs when a payment succeeds
    payment_id = event.payload['data']['object']['id']
    amount = event.payload['data']['object']['amount'] / 100  # Convert from cents
    
    print(f"Payment of ${amount} received! ID: {payment_id}")
    
    # Update your database, send confirmation email, etc.
    return {"status": "processed"}
```

### Step 3: Connect to Your Web Framework

#### Flask Example

```python
from flask import Flask
from smart_api_integrations.frameworks.flask import register_webhook_routes

app = Flask(__name__)

# Register webhook routes
register_webhook_routes(app)

# Start your server
if __name__ == "__main__":
    app.run(port=5000)
```

#### FastAPI Example

```python
from fastapi import FastAPI
from smart_api_integrations.frameworks.fastapi import register_webhook_routes

app = FastAPI()

# Register webhook routes
register_webhook_routes(app)

# Start with: uvicorn app:app --reload
```

Now your application can receive and process webhook events from other services!

## 🛠️ CLI Reference

### Provider Management
```bash
# Add new provider
smart-api-integrations add-provider --name myapi --base-url https://api.example.com

# Generate endpoints from documentation  
smart-api-integrations add-endpoints myapi --url https://docs.example.com/api

# List all providers
smart-api-integrations list-providers
```

### Webhook Management
```bash
# Add webhook configuration to a provider
smart-api-integrations add-webhook github --event push --secret-env GITHUB_WEBHOOK_SECRET

# Generate webhook handler class
smart-api-integrations generate-webhook-handler github --events push pull_request --output-file ./handlers/github_handler.py
```

```python
# Generate a GitHub webhook handler class
from smart_api_integrations.webhooks import generate_webhook_handler, get_webhook_routes

# Generate handler class with event methods
GitHubHandler = generate_webhook_handler('github', events=['push', 'pull_request'])

# Extend with custom logic
class MyGitHubHandler(GitHubHandler):
    def on_push(self, event):
        print(f"Received push to {event.payload['repository']['name']}")
        return self.success_response({'processed': True})

# Instantiate handler
handler = MyGitHubHandler()

# Integrate with your framework
from flask import Flask
app = Flask(__name__)
app.register_blueprint(get_webhook_routes('flask'))
```

[📘 Quick Start](src/webhooks/README.md) | [🔍 Integration Guide](docs/webhook_integration_guide.md) | [⚡ Integration Example](examples/webhook_integration_example.py)

### Code Generation
```bash
# Generate type stubs for IDE support
smart-api-integrations generate-type-stubs myapi

# Generate dedicated client class
smart-api-integrations generate-client myapi --output-file ./clients/myapi.py

# Test provider configuration
smart-api-integrations test myapi --endpoint get_user
```

## 🔐 Authentication Types

Smart API Integrations supports all common authentication methods with automatic environment variable handling.

### Environment Variable Naming Convention

All environment variables follow the pattern `{PROVIDER_NAME}_{AUTH_FIELD}`:

| Auth Type | Environment Variables | Override Parameters |
|-----------|----------------------|-------------------|
| Bearer Token | `{PROVIDER}_TOKEN` | `token_value` |
| API Key | `{PROVIDER}_API_KEY` | `api_key_value` |
| Basic Auth | `{PROVIDER}_USERNAME`, `{PROVIDER}_PASSWORD` | `username`, `password` |
| OAuth2 | `{PROVIDER}_CLIENT_ID`, `{PROVIDER}_CLIENT_SECRET` | `oauth2_client_id`, `oauth2_client_secret` |
| JWT | `{PROVIDER}_JWT_TOKEN` | `jwt_token` |

**Examples**: `GITHUB_TOKEN`, `STRIPE_API_KEY`, `MYAPI_CLIENT_ID`, `SALESFORCE_JWT_TOKEN`

### Real-World Examples

```bash
# Different providers, different auth types
export GITHUB_TOKEN="ghp_your_github_token"                    # GitHub: Bearer token
export STRIPE_API_KEY="sk_test_your_stripe_key"               # Stripe: API key
export SALESFORCE_CLIENT_ID="your_salesforce_client_id"       # Salesforce: OAuth2
export SALESFORCE_CLIENT_SECRET="your_salesforce_secret"      # Salesforce: OAuth2
export FIREBASE_JWT_TOKEN="your_firebase_jwt"                 # Firebase: JWT
export TWILIO_USERNAME="your_twilio_sid"                      # Twilio: Basic auth
export TWILIO_PASSWORD="your_twilio_auth_token"               # Twilio: Basic auth
```

```python
# Each client automatically uses its provider-specific environment variables
github = GithubAPIClient()        # Uses GITHUB_TOKEN
stripe = StripeAPIClient()        # Uses STRIPE_API_KEY
salesforce = SalesforceAPIClient() # Uses SALESFORCE_CLIENT_ID + SALESFORCE_CLIENT_SECRET
firebase = FirebaseAPIClient()    # Uses FIREBASE_JWT_TOKEN
twilio = TwilioAPIClient()        # Uses TWILIO_USERNAME + TWILIO_PASSWORD

# Or override any authentication
github = GithubAPIClient(token_value='custom_token')
salesforce = SalesforceAPIClient(
    oauth2_client_id='custom_id',
    oauth2_client_secret='custom_secret'
)
```

### Bearer Token (GitHub, OpenAI, etc.)
```yaml
# Provider config
auth:
  type: bearer_token
  token_value: ${GITHUB_TOKEN}
```

```bash
# Environment variable
export GITHUB_TOKEN="ghp_your_github_token"
```

```python
# Usage - automatically uses GITHUB_TOKEN
github = GithubAPIClient()

# Or override
github = GithubAPIClient(token_value='custom_token')
```

### API Key in Header (Stripe, etc.)
```yaml
# Provider config
auth:
  type: api_key
  key_name: Authorization
  key_value: Bearer ${STRIPE_API_KEY}
```

```bash
# Environment variable
export STRIPE_API_KEY="sk_test_your_stripe_key"
```

```python
# Usage - automatically uses STRIPE_API_KEY
stripe = StripeAPIClient()

# Or override
stripe = StripeAPIClient(api_key_value='sk_test_custom_key')
```

### API Key in Query (OpenWeatherMap, etc.)
```yaml
# Provider config
auth:
  type: api_key
  key_name: appid
  key_value: ${OPENWEATHERMAP_API_KEY}
  location: query
```

```bash
# Environment variable
export OPENWEATHERMAP_API_KEY="your_api_key"
```

### Basic Authentication
```yaml
# Provider config
auth:
  type: basic
  username: ${MYAPI_USERNAME}
  password: ${MYAPI_PASSWORD}
```

```bash
# Environment variables
export MYAPI_USERNAME="your_username"
export MYAPI_PASSWORD="your_password"
```

```python
# Usage - automatically uses environment variables
api = MyAPIClient()

# Or override
api = MyAPIClient(username='custom_user', password='custom_pass')
```

### OAuth2 Client Credentials
```yaml
# Provider config
auth:
  type: oauth2
  oauth2_client_id: ${MYAPI_CLIENT_ID}
  oauth2_client_secret: ${MYAPI_CLIENT_SECRET}
  oauth2_token_url: https://api.service.com/oauth/token
```

```bash
# Environment variables (provider-specific)
export MYAPI_CLIENT_ID="your_client_id"
export MYAPI_CLIENT_SECRET="your_client_secret"
```

```python
# Usage - automatically uses MYAPI_CLIENT_ID and MYAPI_CLIENT_SECRET
api = MyAPIClient()

# Or override
api = MyAPIClient(
    oauth2_client_id='custom_client_id',
    oauth2_client_secret='custom_client_secret'
)
```

### JWT Token
```yaml
# Provider config
auth:
  type: jwt
  jwt_token: ${MYAPI_JWT_TOKEN}
```

```bash
# Environment variable (provider-specific)
export MYAPI_JWT_TOKEN="your_jwt_token"
```

```python
# Usage - automatically uses MYAPI_JWT_TOKEN
api = MyAPIClient()

# Or override
api = MyAPIClient(jwt_token='custom_jwt_token')
```

### 🔑 Authentication Summary

✅ **Provider-Specific**: Each provider uses its own environment variables  
✅ **Override Support**: All auth parameters can be overridden during initialization  
✅ **Multiple Auth Types**: Bearer Token, API Key, Basic Auth, OAuth2, JWT  
✅ **Automatic Detection**: Auth type determined from provider configuration  
✅ **IDE Support**: Full type hints for all authentication parameters

## 🔄 Complete Workflow

Here's the complete workflow for adding a new API provider:

### 1. Add Provider Configuration

```bash
# Option A: Manual configuration
mkdir -p providers/myapi
cat > providers/myapi/config.yaml << EOF
name: myapi
base_url: https://api.myservice.com/v1
description: My API Service
auth:
  type: bearer_token
  token_value: \${MYAPI_TOKEN}
endpoints:
  get_user:
    path: /users/{user_id}
    method: GET
    parameters:
      user_id: {type: string, required: true, in: path}
EOF

# Option B: Use CLI to generate from docs
smart-api-integrations add-endpoints myapi --url "https://docs.myservice.com/api" --max-endpoints 10
```

### 2. Set Authentication

```bash
# Set environment variables based on auth type (provider-specific)
export MYAPI_TOKEN="your_api_token"                    # For bearer_token
# export MYAPI_API_KEY="your_key"                      # For api_key
# export MYAPI_USERNAME="user"                         # For basic auth
# export MYAPI_PASSWORD="pass"                         # For basic auth
# export MYAPI_CLIENT_ID="client_id"                   # For oauth2
# export MYAPI_CLIENT_SECRET="client_secret"           # For oauth2
# export MYAPI_JWT_TOKEN="jwt_token"                   # For jwt
```

### 3. Generate Client Class

```bash
# Generate a dedicated client class
smart-api-integrations generate-client myapi \
    --class-name "MyAPIClient" \
    --output-file "./clients/myapi_client.py"
```

### 4. Generate Type Stubs (Optional)

```bash
# Generate type stubs for IDE support
smart-api-integrations generate-type-stubs --provider myapi --output-dir "./typings"

# For the GitHub sample provider:
smart-api-integrations generate-type-stubs --provider github --output-dir "./typings"
```

### 5. Use the Client

```python
from clients.myapi_client import MyAPIClient

# Automatically uses provider-specific environment variables
client = MyAPIClient()  # Uses MYAPI_TOKEN (or MYAPI_CLIENT_ID + MYAPI_CLIENT_SECRET for OAuth2)

# Or override authentication (works for all auth types)
client = MyAPIClient(token_value='custom_token')                    # Bearer token override
# client = MyAPIClient(api_key_value='custom_key')                 # API key override
# client = MyAPIClient(username='user', password='pass')           # Basic auth override
# client = MyAPIClient(                                            # OAuth2 override
#     oauth2_client_id='custom_id',
#     oauth2_client_secret='custom_secret'
# )
# client = MyAPIClient(jwt_token='custom_jwt')                     # JWT override

# Make API calls with full IDE support
user = client.get_user(user_id='123')
print(f"User: {user.data['name']}")
```

## 📦 Local Development Setup

### 1. Install for Development

```bash
# Install the package in development mode
git clone https://github.com/yourusername/smart-api-integrations.git
cd smart-api-integrations
pip install -e .
```

### 2. Create Your Project Structure

```
my_project/
├── providers/           # API configurations
│   ├── myapi/
│   │   └── config.yaml
│   └── stripe/
│       └── config.yaml
├── clients/             # Custom client classes
│   ├── __init__.py
│   ├── myapi_client.py
│   └── stripe_client.py
├── typings/             # Generated type stubs
│   ├── myapi.pyi
│   └── stripe.pyi
└── main.py             # Your application
```

### 3. Environment Configuration

```bash
# .env file
SMART_API_INTEGRATIONS_PROVIDERS_DIR="./providers"
GITHUB_TOKEN="your_github_token"
STRIPE_API_KEY="your_stripe_key"
MYAPI_TOKEN="your_api_token"
```

### 4. Use in Your Application

```python
# main.py
import os
from dotenv import load_dotenv
from clients.myapi_client import MyAPIClient
from clients.stripe_client import StripeClient

load_dotenv()

# Initialize clients
myapi = MyAPIClient()
stripe = StripeClient()

# Use with full IDE support
users = myapi.list_users(limit=10)
customers = stripe.list_customers(limit=5)
```

## 🧪 Testing Your Integration

```python
# Test your custom client
def test_myapi_integration():
    client = MyAPIClient()
    
    # Test endpoint availability
    methods = client.list_available_methods()
    assert 'get_user' in methods
    
    # Test actual API call (with real token)
    user = client.get_user(user_id='test_user')
    assert user.success
    assert 'name' in user.data

# Run tests
pytest tests/
```

## 🎯 Key Benefits

- ✅ **Zero Boilerplate**: Define endpoints once, use everywhere
- ✅ **Type Safety**: Full IDE support with generated type stubs  
- ✅ **Intelligent Parameters**: Automatic routing of path/query/body parameters
- ✅ **Custom Logic**: Easy to extend with business-specific methods
- ✅ **Production Ready**: Built-in error handling, retries, rate limiting
- ✅ **AI Assistance**: Generate endpoints from documentation URLs
- ✅ **Webhook Support**: Easily handle incoming webhook events
- ✅ **Framework Integration**: Works with Flask, FastAPI, and Django

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: 
  - [Provider Integration Guide](docs/new_provider_integration_guide.md)
  - [Webhook Integration Guide](docs/webhook_integration_guide.md)
- **Examples**: 
  - [API Examples](examples/github_basic_example.py)
  - [Webhook Examples](examples/github_webhook_example.py)
  - [Flask Integration](examples/flask_webhook_example.py)
- **Issues**: [GitHub Issues](https://github.com/yourusername/smart-api-integrations/issues)

---

**Stop writing API boilerplate. Start building features.** 🚀

```bash
pip install smart-api-integrations
```

# Smart API Integrations

Connect to any third-party API or receive webhook events without writing boilerplate code.

## What This Library Does

### For API Requests (Outgoing)
This library turns any API into simple function calls, like having an official SDK for any service.

Instead of writing:
```python
# Without Smart API Integrations
import requests
headers = {"Authorization": f"Bearer {token}"}
response = requests.get("https://api.example.com/users/123", headers=headers)
if response.status_code == 200:
    user = response.json()
else:
    raise Exception(f"API error: {response.status_code}")
```

You can write:
```python
# With Smart API Integrations
client = UniversalAPIClient("example")
user = client.get_user(user_id=123)  # That's it!
```

### For Webhooks (Incoming)
When services need to send data to your application (like payment notifications), this library:
1. Sets up the URLs where services can send data
2. Verifies the data is legitimate (not fake)
3. Routes each event type to your specific handler function

Instead of writing security, routing, and parsing code, just write what should happen for each event:
```python
@processor.on("payment.succeeded")
def handle_payment(event):
    print(f"Payment received: ${event.payload['amount']}")
    # Update your database, send email, etc.
```

## Features

- **Turn Any API into Function Calls**: Use any API like it has an official SDK
- **OpenAPI Support**: Instantly create clients from API documentation
- **Smart Parameter Handling**: Automatically puts parameters in the right place (URL, query, body)
- **Built-in Security**: Handles authentication, signatures, and tokens
- **Error Protection**: Automatic retries and rate limiting
- **Webhook Receiver**: Secure endpoint creation for incoming data
- **Framework Ready**: Works with Flask, Django, or FastAPI

## Installation

```bash
pip install smart-api-integrations
```

## Quick Start

### Using with YAML Configuration

```python
from smart_api_integrations import UniversalAPIClient

# Create a client for the GitHub API
client = UniversalAPIClient("github")

# List repositories for the authenticated user
response = client.list_repos()
print(response.data)
```

### Using with OpenAPI Specification

```python
from smart_api_integrations import UniversalAPIClient
from smart_api_integrations.cli.openapi_converter import convert_openapi_to_config

# Convert OpenAPI specification to config.yaml (one-time operation)
config_file = convert_openapi_to_config(
    "https://petstore3.swagger.io/api/v3/openapi.json",
    output_dir="path/to/providers",
    provider_name="petstore"
)

# Create a client using the generated config.yaml
client = UniversalAPIClient("petstore")

# Call methods using snake_case
pet = client.get_pet_by_id(petId=1)
print(pet.data)

# Or using the original camelCase operationId
pet = client.getPetById(petId=1)
print(pet.data)
```

### Using Webhooks

First, create a configuration file for the service sending webhooks:

```yaml
# providers/stripe/webhook.yaml
webhooks:
  default:
    path: /webhooks/stripe/
    verify_signature: true
    signing_secret_env: STRIPE_WEBHOOK_SECRET
```

Then set up your webhook handlers:

```python
from smart_api_integrations.core.webhook_registry import get_webhook_registry

# Step 1: Create a webhook processor
registry = get_webhook_registry()
processor = registry.create_processor("stripe", "default")

# Step 2: Add handlers for different event types
@processor.on("payment.succeeded")
def handle_payment_succeeded(event):
    # This runs when a payment succeeds
    order_id = event.payload["data"]["object"]["metadata"]["order_id"]
    amount = event.payload["data"]["object"]["amount"]
    
    print(f"Payment of ${amount/100} received for order {order_id}")
    # Update order status in database, send confirmation email, etc.
    return {"status": "processed"}

@processor.on("payment.failed")
def handle_payment_failed(event):
    # This runs when a payment fails
    order_id = event.payload["data"]["object"]["metadata"]["order_id"]
    print(f"Payment failed for order {order_id}")
    # Update order status, notify customer, etc.
    return {"status": "handled"}

# Step 3: Connect to your web framework (Flask example)
from flask import Flask
from smart_api_integrations.frameworks.flask import register_webhook_routes

app = Flask(__name__)
register_webhook_routes(app)  # Creates URLs like /webhooks/stripe/

# Step 4: Start your server
app.run()
```

The library handles:
- Creating secure URLs for each service
- Verifying webhook signatures
- Parsing event data
- Routing to the right handler function
- Sending proper responses back

## Documentation

### Getting Started Guides
- [Using OpenAPI Specifications](docs/openapi_integration.md) - Create API clients from API documentation
- [Setting Up Webhooks](docs/webhook_integration.md) - Receive and process events from third-party services

### Common Use Cases
- Connect to payment providers (Stripe, PayPal)
- Integrate with CRM systems (Salesforce, HubSpot)
- Use social media APIs (Twitter, Facebook)
- Receive notifications (webhooks) when events happen

## Examples

- [OpenAPI Converter Example](examples/openapi_converter_example.py)
- [Webhook Handler Example](examples/webhook_handler_example.py)
