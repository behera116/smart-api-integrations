# Smart API Integrations

A universal API integration system with dynamic client generation, flexible authentication, and comprehensive webhook handling.

[![PyPI version](https://badge.fury.io/py/smart-api-integrations.svg)](https://badge.fury.io/py/smart-api-integrations)
[![Python Support](https://img.shields.io/pypi/pyversions/smart-api-integrations.svg)](https://pypi.org/project/smart-api-integrations/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation Status](https://readthedocs.org/projects/smart-api-integrations/badge/?version=latest)](https://smart-api-integrations.readthedocs.io/en/latest/?badge=latest)

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Integration with Existing Projects](#integration-with-existing-projects)
- [Adding New Providers](#adding-new-providers)
- [Adding Webhooks](#adding-webhooks)
- [Framework Integration](#framework-integration)
- [CLI Commands](#cli-commands)
- [Advanced Features](#advanced-features)
- [Examples](#examples)
- [Contributing](#contributing)

## Features

- 🚀 **Dynamic Client Generation** - Auto-generate Python methods from API configurations
- 🔐 **Multiple Auth Methods** - Bearer, API Key, OAuth2, Basic, JWT support
- 🪝 **Webhook Handling** - Built-in webhook verification and routing
- 🔄 **Standardized Responses** - Consistent response format across all APIs
- ⚡ **Async Support** - Both sync and async operations
- 🛡️ **Type Safety** - Full type hints and IDE support
- 📦 **Framework Agnostic** - Use with Django, Flask, FastAPI, or standalone
- 🤖 **AI-Powered** - Generate endpoints from documentation using OpenAI
- 📜 **OpenAPI Support** - Import and use OpenAPI specifications

## Installation

### Basic Installation

```bash
# Core package (framework-agnostic)
pip install smart-api-integrations
```

### Framework-Specific Installation

```bash
# For Django projects
pip install smart-api-integrations[django]

# For Flask projects
pip install smart-api-integrations[flask]

# For FastAPI projects
pip install smart-api-integrations[fastapi]
```

### Optional Features

```bash
# AI-powered endpoint generation
pip install smart-api-integrations[ai]

# OpenAPI specification support
pip install smart-api-integrations[openapi]

# Everything included
pip install smart-api-integrations[all]
```

## Quick Start

### 1. Install Smart API

```bash
pip install smart-api-integrations
```

### 2. Create Your First Provider

```bash
# Using CLI (recommended)
smart-api add-provider --name github --base-url https://api.github.com --auth bearer_token

# This creates: providers/github/config.yaml
```

### 3. Set Environment Variables

```bash
export GITHUB_TOKEN="your-github-token-here"
```

### 4. Use the Client

```python
from smart_api_integrations import SmartAPIClient

# Initialize client
github = SmartAPIClient('github')

# Make API calls with full IDE support
user = github.get_user()
print(f"Logged in as: {user.data['login']}")

repos = github.list_repos(params={'per_page': 10})
for repo in repos.data:
    print(f"- {repo['name']}")
```

## Integration with Existing Projects

### Step 1: Install in Your Project

```bash
cd your-existing-project
pip install smart-api-integrations
```

### Step 2: Create Providers Directory

```bash
# Create providers directory in your project root
mkdir -p providers
```

### Step 3: Add Your First Provider

```bash
# Example: Adding Stripe API
smart-api add-provider \
  --name stripe \
  --base-url https://api.stripe.com/v1 \
  --auth bearer_token \
  --description "Stripe Payment API"
```

This creates `providers/stripe/config.yaml`:

```yaml
name: "stripe"
base_url: "https://api.stripe.com/v1"
description: "Stripe Payment API"
auth:
  type: "bearer_token"
  token_value: "${STRIPE_SECRET_KEY}"
endpoints: {}
```

### Step 4: Set Environment Variables

```bash
# Add to your .env file or environment
export STRIPE_SECRET_KEY="sk_test_your_stripe_key"
export GITHUB_TOKEN="ghp_your_github_token"
```

### Step 5: Start Using APIs

```python
from smart_api_integrations import SmartAPIClient

# Use any configured provider
stripe = SmartAPIClient('stripe')
github = SmartAPIClient('github')

# Make API calls
customers = stripe.list_customers()
user = github.get_user()
```

## Adding New Providers

### Method 1: Using CLI (Recommended)

```bash
# Interactive mode
smart-api add-provider --name myapi --base-url https://api.example.com --interactive

# Non-interactive with options
smart-api add-provider \
  --name shopify \
  --base-url https://your-shop.myshopify.com/admin/api/2023-04 \
  --auth api_key \
  --description "Shopify Admin API"
```

### Method 2: Manual Configuration

Create `providers/myapi/config.yaml`:

```yaml
name: "myapi"
base_url: "https://api.example.com"
description: "My Custom API"
version: "1.0"

auth:
  type: "bearer_token"  # or api_key, basic, oauth2, jwt, none
  token_value: "${MYAPI_TOKEN}"

default_headers:
  Content-Type: "application/json"
  User-Agent: "MyApp/1.0"

endpoints:
  list_items:
    path: "/items"
    method: "GET"
    description: "Get all items"
    parameters:
      page:
        type: "integer"
        required: false
        in: "query"
      
  create_item:
    path: "/items"
    method: "POST"
    description: "Create a new item"
    
  get_item:
    path: "/items/{item_id}"
    method: "GET"
    description: "Get specific item"
    parameters:
      item_id:
        type: "string"
        required: true
        in: "path"
```

### Authentication Types

Smart API supports multiple authentication methods:

```yaml
# Bearer Token (GitHub, OpenAI, etc.)
auth:
  type: "bearer_token"
  token_value: "${API_TOKEN}"

# API Key in Header
auth:
  type: "api_key"
  api_key_header: "X-API-Key"
  api_key_value: "${API_KEY}"

# API Key in Query Parameter
auth:
  type: "api_key"
  api_key_param: "api_key"
  api_key_value: "${API_KEY}"

# Basic Authentication
auth:
  type: "basic"
  username: "${API_USERNAME}"
  password: "${API_PASSWORD}"

# OAuth2 Client Credentials
auth:
  type: "oauth2"
  oauth2_client_id: "${CLIENT_ID}"
  oauth2_client_secret: "${CLIENT_SECRET}"
  oauth2_token_url: "https://api.example.com/oauth/token"

# JWT Token
auth:
  type: "jwt"
  jwt_token: "${JWT_TOKEN}"

# No Authentication
auth:
  type: "none"
```

### Auto-Generate Endpoints

```bash
# From OpenAPI specification
smart-api add-endpoints --provider myapi --spec openapi.yaml

# Using AI (requires openai package)
smart-api add-endpoints --provider github --url https://docs.github.com/en/rest

# Add example endpoints
smart-api add-endpoints --provider myapi
```

## Adding Webhooks

### Step 1: Create Webhook Configuration

Create `providers/stripe/webhook.yaml`:

```yaml
provider: "stripe"
webhooks:
  payment_intent.succeeded:
    description: "Payment completed successfully"
    verification:
      type: "stripe_signature"
      secret: "${STRIPE_WEBHOOK_SECRET}"
      
  customer.created:
    description: "New customer created"
    verification:
      type: "stripe_signature"
      secret: "${STRIPE_WEBHOOK_SECRET}"

security:
  allowed_ips: []  # Empty = allow all
  require_https: true
  max_age_seconds: 300
```

### Step 2: Create Webhook Handlers

```python
from smart_api_integrations.webhooks import webhook_handler

@webhook_handler('stripe', 'payment_intent.succeeded')
def handle_payment_success(event):
    """Handle successful payment."""
    payment = event.payload['data']['object']
    amount = payment['amount'] / 100
    
    print(f"Payment of ${amount} succeeded!")
    
    # Your business logic here
    # - Update database
    # - Send confirmation email
    # - Trigger fulfillment
    
    return {'processed': True, 'payment_id': payment['id']}

@webhook_handler('stripe', 'customer.created')
def handle_new_customer(event):
    """Handle new customer creation."""
    customer = event.payload['data']['object']
    
    print(f"New customer: {customer['email']}")
    
    # Your business logic here
    # - Add to CRM
    # - Send welcome email
    # - Set up onboarding
    
    return {'processed': True, 'customer_id': customer['id']}
```

### Step 3: Test Webhooks

```bash
# Test webhook handlers
smart-api test-webhook --provider stripe --webhook payment_intent.succeeded

# Test with custom payload
smart-api test-webhook --provider stripe --webhook customer.created --payload '{"data": {"object": {"id": "cus_123", "email": "test@example.com"}}}'
```

## Framework Integration

### Django Integration

#### 1. Add to settings.py

```python
INSTALLED_APPS = [
    # ... your apps
    'smart_api_integrations',
]

# Optional: Configure Smart API
SMART_API_INTEGRATIONS_PROVIDERS_DIR = BASE_DIR / 'providers'
SMART_API_INTEGRATIONS_AUTO_DISCOVER_WEBHOOKS = True
```

#### 2. Add to urls.py

```python
from django.urls import path, include
from smart_api_integrations.frameworks.django import get_django_urls

urlpatterns = [
    # ... your URLs
    path('api/webhooks/', include(get_django_urls())),
]
```

#### 3. Use in views

```python
from django.http import JsonResponse
from smart_api_integrations import SmartAPIClient

def my_view(request):
    github = SmartAPIClient('github')
    user = github.get_user()
    
    return JsonResponse({
        'user': user.data,
        'status': user.status_code
    })
```

#### 4. Management Commands

```bash
# Django management commands are automatically available
python manage.py add_provider --name myapi --base-url https://api.example.com
python manage.py test_webhook --provider stripe --webhook payment_intent.succeeded
```

### Flask Integration

#### 1. Initialize Flask App

```python
from flask import Flask
from smart_api_integrations.frameworks.flask import init_flask_app

app = Flask(__name__)

# Initialize Smart API
init_flask_app(app, url_prefix='/api')

@app.route('/github-user')
def github_user():
    from smart_api_integrations import SmartAPIClient
    github = SmartAPIClient('github')
    user = github.get_user()
    return {'user': user.data}

if __name__ == '__main__':
    app.run(debug=True)
```

#### 2. Manual Blueprint Registration

```python
from flask import Flask
from smart_api_integrations.frameworks.flask import create_flask_blueprint

app = Flask(__name__)

# Create and register webhook blueprint
webhook_bp = create_flask_blueprint()
app.register_blueprint(webhook_bp, url_prefix='/api')
```

#### 3. Flask CLI Commands

```bash
# Flask CLI commands (if flask-cli is installed)
flask add-provider --name myapi --base-url https://api.example.com
flask test-webhook --provider stripe --webhook payment_intent.succeeded
```

### FastAPI Integration

#### 1. Add to FastAPI App

```python
from fastapi import FastAPI
from smart_api_integrations.frameworks.fastapi import create_fastapi_router
from smart_api_integrations import SmartAPIClient

app = FastAPI()

# Include webhook router
webhook_router = create_fastapi_router()
app.include_router(webhook_router, prefix="/api")

@app.get("/github-user")
async def get_github_user():
    github = SmartAPIClient('github')
    user = github.get_user()
    return {"user": user.data}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

#### 2. Async Support (Coming Soon)

```python
# Future async support
@app.get("/github-repos")
async def get_repos():
    github = AsyncSmartAPIClient('github')
    repos = await github.list_repos()
    return {"repos": repos.data}
```

### Standalone Usage (No Framework)

```python
from smart_api_integrations import SmartAPIClient
from smart_api_integrations.webhooks.base import BaseWebhookHandler, SimpleWebhookRequest
import json

# Use API clients
github = SmartAPIClient('github')
stripe = SmartAPIClient('stripe')

# Process webhooks manually
webhook_handler = BaseWebhookHandler()

def process_webhook(provider, webhook_name, body, headers):
    request = SimpleWebhookRequest(
        body=body.encode('utf-8'),
        headers=headers,
        method='POST'
    )
    
    response = webhook_handler.process_webhook(request, provider, webhook_name)
    return response.data, response.status_code
```

## CLI Commands

Smart API provides a comprehensive CLI for managing providers and webhooks:

### Provider Management

```bash
# List all providers
smart-api list-providers

# Add new provider
smart-api add-provider --name myapi --base-url https://api.example.com --auth bearer_token

# Interactive provider creation
smart-api add-provider --name myapi --base-url https://api.example.com --interactive
```

### Endpoint Management

```bash
# Add example endpoints
smart-api add-endpoints --provider myapi

# Generate from OpenAPI spec
smart-api add-endpoints --provider myapi --spec openapi.yaml

# Generate using AI (requires [ai] extra)
smart-api add-endpoints --provider github --url https://docs.github.com/en/rest
```

### Webhook Testing

```bash
# Test webhook with default payload
smart-api test-webhook --provider stripe --webhook payment_intent.succeeded

# Test with custom payload
smart-api test-webhook --provider stripe --webhook customer.created --payload '{"test": "data"}'
```

### Utility Commands

```bash
# Check available dependencies
smart-api check-deps

# Show version
smart-api --version
```

## Advanced Features

### Environment Variable Support

All configuration values support environment variable substitution:

```yaml
auth:
  type: "bearer_token"
  token_value: "${API_TOKEN}"  # Will use $API_TOKEN environment variable

base_url: "${API_BASE_URL:-https://api.example.com}"  # With default value
```

### Custom Headers and Timeouts

```yaml
default_headers:
  User-Agent: "MyApp/1.0"
  Accept: "application/json"

default_timeout: 30.0  # seconds

endpoints:
  slow_endpoint:
    path: "/slow"
    method: "GET"
    timeout: 60.0  # Override default timeout
```

### Rate Limiting and Retries

```yaml
rate_limit:
  requests_per_second: 10
  burst_limit: 20

retry:
  max_retries: 3
  backoff_factor: 0.3
  retry_on_status: [429, 500, 502, 503, 504]
```

### Type Safety

Smart API provides full type hints for better IDE support:

```python
from smart_api_integrations import SmartAPIClient
from smart_api_integrations.core import APIResponse

github: SmartAPIClient = SmartAPIClient('github')
response: APIResponse = github.get_user()

# Full autocomplete and type checking
user_login: str = response.data['login']
status_code: int = response.status_code
```

## Examples

### Complete E-commerce Integration

```python
from smart_api_integrations import SmartAPIClient
from smart_api_integrations.webhooks import webhook_handler

# Initialize clients
stripe = SmartAPIClient('stripe')
shopify = SmartAPIClient('shopify')
mailchimp = SmartAPIClient('mailchimp')

@webhook_handler('stripe', 'payment_intent.succeeded')
def handle_payment(event):
    payment = event.payload['data']['object']
    
    # 1. Update order in Shopify
    order = shopify.get_order(payment['metadata']['order_id'])
    shopify.update_order(order['id'], {'financial_status': 'paid'})
    
    # 2. Add customer to email list
    customer_email = payment['receipt_email']
    mailchimp.add_subscriber('customers', {'email': customer_email})
    
    # 3. Send confirmation
    send_order_confirmation(payment['metadata']['order_id'])
    
    return {'processed': True}

def create_subscription(customer_email, plan_id):
    """Create a subscription across multiple services."""
    
    # Create customer in Stripe
    customer = stripe.create_customer({
        'email': customer_email,
        'description': 'Subscription customer'
    })
    
    # Create subscription
    subscription = stripe.create_subscription({
        'customer': customer.data['id'],
        'items': [{'price': plan_id}]
    })
    
    # Add to email marketing
    mailchimp.add_subscriber('subscribers', {
        'email': customer_email,
        'tags': ['subscriber', f'plan_{plan_id}']
    })
    
    return subscription.data
```

### Multi-API Data Sync

```python
def sync_customer_data():
    """Sync customer data across multiple platforms."""
    
    # Get customers from Stripe
    stripe_customers = stripe.list_customers()
    
    for customer in stripe_customers.data:
        # Check if exists in CRM
        crm_contact = hubspot.search_contacts(customer['email'])
        
        if not crm_contact.data['results']:
            # Create in HubSpot
            hubspot.create_contact({
                'email': customer['email'],
                'firstname': customer.get('name', '').split(' ')[0],
                'stripe_customer_id': customer['id']
            })
        
        # Add to email list if not exists
        try:
            mailchimp.add_subscriber('all_customers', {
                'email': customer['email'],
                'status': 'subscribed'
            })
        except Exception:
            pass  # Already exists
```

## Project Structure

When using Smart API in your project, organize it like this:

```
your-project/
├── providers/                    # API configurations
│   ├── github/
│   │   ├── config.yaml          # API endpoints
│   │   └── webhook.yaml         # Webhook config
│   ├── stripe/
│   │   ├── config.yaml
│   │   └── webhook.yaml
│   └── shopify/
│       └── config.yaml
├── webhooks/                     # Webhook handlers
│   ├── __init__.py
│   ├── stripe_handlers.py
│   ├── github_handlers.py
│   └── shopify_handlers.py
├── services/                     # Business logic
│   ├── payment_service.py
│   └── order_service.py
├── .env                         # Environment variables
└── requirements.txt
```

## Troubleshooting

### Common Issues

1. **Provider not found**
   ```bash
   # Make sure providers directory exists and has config.yaml
   ls -la providers/myapi/
   ```

2. **Authentication errors**
   ```bash
   # Check environment variables
   echo $GITHUB_TOKEN
   echo $STRIPE_SECRET_KEY
   ```

3. **Webhook signature verification fails**
   ```bash
   # Verify webhook secret is correct
   smart-api test-webhook --provider stripe --webhook payment_intent.succeeded
   ```

4. **Import errors**
   ```bash
   # Check dependencies
   smart-api check-deps
   pip install smart-api-integrations[all]
   ```

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from smart_api_integrations import SmartAPIClient
github = SmartAPIClient('github')
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/anandabehera/smart-api-integrations.git
cd smart-api-integrations

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
black src
flake8 src
mypy src
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 📧 Email: behera.anand1@gmail.com
- 🐛 Issues: [GitHub Issues](https://github.com/anandabehera/smart-api-integrations/issues)
- 📖 Documentation: [Full Documentation](https://smart-api-integrations.readthedocs.io)

## Acknowledgments

Smart API Integrations was inspired by the need for a simple, yet powerful way to integrate with multiple APIs without writing boilerplate code. Special thanks to the open-source community for their contributions and feedback.
