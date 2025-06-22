# New API Provider Integration Guide

## 🚀 Overview

The `smart-api-integrations` package provides a powerful framework for integrating any REST API provider with minimal configuration. This guide shows you how to add new API providers and use them seamlessly.

## 📦 Installation

```bash
pip install smart-api-integrations
```

## 🔧 Quick Start: Adding a New Provider

### Step 1: Install the Package

```bash
pip install smart-api-integrations
```

### Step 2: Set Up Environment

```bash
# Set your providers directory
export SMART_API_INTEGRATIONS_PROVIDERS_DIR="./providers"

# Set your API tokens
export STRIPE_API_KEY="sk_test_your_stripe_key"
export TWITTER_API_KEY="your_twitter_key"
export OPENAI_API_KEY="sk-proj-your_openai_key"
```

### Step 3: Create Provider Configuration

```python
# Create a new provider using the CLI
from smart_api_integrations.cli import main

# Or manually create provider configuration
import yaml
from pathlib import Path

# Example: Stripe API Provider
stripe_config = {
    'name': 'stripe',
    'base_url': 'https://api.stripe.com/v1',
    'description': 'Stripe Payment Processing API',
    'auth': {
        'type': 'bearer_token',
        'token_value': '${STRIPE_API_KEY}'
    },
    'default_headers': {
        'Content-Type': 'application/x-www-form-urlencoded'
    },
    'endpoints': {
        'list_customers': {
            'path': '/customers',
            'method': 'GET',
            'description': 'List all customers',
            'parameters': {
                'limit': {
                    'type': 'integer',
                    'required': False,
                    'in': 'query',
                    'description': 'Number of customers to return (1-100)'
                },
                'starting_after': {
                    'type': 'string',
                    'required': False,
                    'in': 'query',
                    'description': 'Cursor for pagination'
                }
            }
        },
        'create_customer': {
            'path': '/customers',
            'method': 'POST',
            'description': 'Create a new customer',
            'parameters': {
                'email': {
                    'type': 'string',
                    'required': True,
                    'in': 'body',
                    'description': 'Customer email address'
                },
                'name': {
                    'type': 'string',
                    'required': False,
                    'in': 'body',
                    'description': 'Customer full name'
                },
                'description': {
                    'type': 'string',
                    'required': False,
                    'in': 'body',
                    'description': 'Customer description'
                }
            }
        },
        'get_customer': {
            'path': '/customers/{customer_id}',
            'method': 'GET',
            'description': 'Retrieve a customer by ID',
            'parameters': {
                'customer_id': {
                    'type': 'string',
                    'required': True,
                    'in': 'path',
                    'description': 'Unique customer identifier'
                }
            }
        },
        'update_customer': {
            'path': '/customers/{customer_id}',
            'method': 'POST',
            'description': 'Update a customer',
            'parameters': {
                'customer_id': {
                    'type': 'string',
                    'required': True,
                    'in': 'path',
                    'description': 'Customer ID to update'
                },
                'email': {
                    'type': 'string',
                    'required': False,
                    'in': 'body',
                    'description': 'Updated email address'
                },
                'name': {
                    'type': 'string',
                    'required': False,
                    'in': 'body',
                    'description': 'Updated customer name'
                }
            }
        },
        'delete_customer': {
            'path': '/customers/{customer_id}',
            'method': 'DELETE',
            'description': 'Delete a customer',
            'parameters': {
                'customer_id': {
                    'type': 'string',
                    'required': True,
                    'in': 'path',
                    'description': 'Customer ID to delete'
                }
            }
        }
    }
}

# Save configuration
providers_dir = Path("./providers/stripe")
providers_dir.mkdir(parents=True, exist_ok=True)

with open(providers_dir / "config.yaml", 'w') as f:
    yaml.dump(stripe_config, f, default_flow_style=False)
```

## 🤖 AI-Powered Endpoint Generation

Use the CLI to automatically generate endpoints from API documentation:

```bash
# Generate endpoints using AI
smart-api-integrations add-endpoints stripe \
    --url "https://stripe.com/docs/api" \
    --max-endpoints 10 \
    --model "gpt-4" \
    --output-format yaml
```

## 💻 Using Your New Provider

### Method 1: Universal Client

```python
from smart_api_integrations import UniversalAPIClient

# Initialize client
stripe = UniversalAPIClient('stripe')

# Direct method calls with intelligent parameter handling
customers = stripe.list_customers(limit=10)
print(f"Found {len(customers.data)} customers")

# Create a new customer
new_customer = stripe.create_customer(
    email="john.doe@example.com",
    name="John Doe",
    description="VIP Customer"
)

if new_customer.success:
    customer_id = new_customer.data['id']
    print(f"Created customer: {customer_id}")
    
    # Get the customer
    customer = stripe.get_customer(customer_id=customer_id)
    print(f"Customer: {customer.data['name']} ({customer.data['email']})")
    
    # Update the customer
    updated = stripe.update_customer(
        customer_id=customer_id,
        name="John Smith"
    )
    
    # Delete the customer
    deleted = stripe.delete_customer(customer_id=customer_id)
    print(f"Customer deleted: {deleted.success}")
```

### Method 2: Raw API Calls

```python
# Make raw API calls for custom endpoints
response = stripe.call_raw(
    method='GET',
    path='/balance',
    headers={'Stripe-Version': '2023-10-16'}
)

if response.success:
    print(f"Account balance: {response.data}")
```

## 🔧 Parameter Types Support

The framework intelligently handles all parameter types:

### Path Parameters
```python
# Automatically extracted from URL path
user = api.get_user(user_id="123")  # → /users/123
```

### Query Parameters
```python
# Added to URL query string
users = api.list_users(page=2, limit=50)  # → /users?page=2&limit=50
```

### Body Parameters (JSON)
```python
# Sent as JSON in request body
customer = api.create_customer(
    email="test@example.com",
    name="Test User"
)
```

### Header Parameters
```python
# Added to request headers
data = api.get_data(
    accept="application/json",
    user_agent="MyApp/1.0"
)
```

## 🌟 Advanced Features

### Authentication Types

```python
# Bearer Token
auth_config = {
    'type': 'bearer_token',
    'token_value': '${API_TOKEN}'
}

# API Key in Header
auth_config = {
    'type': 'api_key',
    'key_name': 'X-API-Key',
    'key_value': '${API_KEY}'
}

# API Key in Query
auth_config = {
    'type': 'api_key',
    'key_name': 'api_key',
    'key_value': '${API_KEY}',
    'location': 'query'
}

# Basic Authentication
auth_config = {
    'type': 'basic',
    'username': '${API_USERNAME}',
    'password': '${API_PASSWORD}'
}
```

### Rate Limiting

```python
rate_limit_config = {
    'requests_per_second': 10,
    'requests_per_minute': 100,
    'requests_per_hour': 1000
}
```

### Retry Configuration

```python
retry_config = {
    'max_retries': 3,
    'backoff_factor': 1.0,
    'retry_on_status': [429, 500, 502, 503, 504],
    'retry_on_exceptions': ['ConnectionError', 'Timeout']
}
```

## 📊 Real-World Examples

### Example 1: Twitter API Integration

```python
twitter_config = {
    'name': 'twitter',
    'base_url': 'https://api.twitter.com/2',
    'description': 'Twitter API v2',
    'auth': {
        'type': 'bearer_token',
        'token_value': '${TWITTER_BEARER_TOKEN}'
    },
    'endpoints': {
        'get_user_by_username': {
            'path': '/users/by/username/{username}',
            'method': 'GET',
            'parameters': {
                'username': {'type': 'string', 'required': True, 'in': 'path'},
                'user.fields': {'type': 'string', 'required': False, 'in': 'query'}
            }
        },
        'get_tweets': {
            'path': '/tweets/search/recent',
            'method': 'GET',
            'parameters': {
                'query': {'type': 'string', 'required': True, 'in': 'query'},
                'max_results': {'type': 'integer', 'required': False, 'in': 'query'}
            }
        }
    }
}

# Usage
twitter = UniversalAPIClient('twitter')
user = twitter.get_user_by_username(username="elonmusk")
tweets = twitter.get_tweets(query="python", max_results=10)
```

### Example 2: OpenWeatherMap API

```python
weather_config = {
    'name': 'openweathermap',
    'base_url': 'https://api.openweathermap.org/data/2.5',
    'description': 'OpenWeatherMap API',
    'auth': {
        'type': 'api_key',
        'key_name': 'appid',
        'key_value': '${OPENWEATHERMAP_API_KEY}',
        'location': 'query'
    },
    'endpoints': {
        'get_current_weather': {
            'path': '/weather',
            'method': 'GET',
            'parameters': {
                'q': {'type': 'string', 'required': True, 'in': 'query'},
                'units': {'type': 'string', 'required': False, 'in': 'query'}
            }
        },
        'get_forecast': {
            'path': '/forecast',
            'method': 'GET',
            'parameters': {
                'q': {'type': 'string', 'required': True, 'in': 'query'},
                'cnt': {'type': 'integer', 'required': False, 'in': 'query'}
            }
        }
    }
}

# Usage
weather = UniversalAPIClient('openweathermap')
current = weather.get_current_weather(q="London", units="metric")
forecast = weather.get_forecast(q="London", cnt=5)
```

## 🛠️ CLI Commands

### Add New Provider
```bash
smart-api-integrations add-provider \
    --name "myapi" \
    --base-url "https://api.myservice.com/v1" \
    --auth-type "bearer_token" \
    --token-env "MYAPI_TOKEN"
```

### Generate Endpoints
```bash
smart-api-integrations add-endpoints myapi \
    --url "https://docs.myservice.com/api" \
    --max-endpoints 15 \
    --model "gpt-4" \
    --dry-run
```

### Test Integration
```bash
smart-api-integrations test myapi \
    --endpoint "list_users" \
    --params '{"limit": 5}'
```

### Generate Type Stubs
```bash
smart-api-integrations generate-type-stubs myapi \
    --output-dir "./stubs"
```

## 🔍 Debugging and Testing

### Enable Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Your API calls will now show detailed logs
api = UniversalAPIClient('myapi')
result = api.some_endpoint()
```

### Test Webhooks
```bash
smart-api-integrations test-webhook \
    --provider "myapi" \
    --endpoint "/webhooks/test" \
    --payload '{"test": "data"}'
```

## 🚀 Production Deployment

### Environment Variables
```bash
# .env file
SMART_API_INTEGRATIONS_PROVIDERS_DIR="/app/providers"
STRIPE_API_KEY="sk_live_your_live_key"
GITHUB_TOKEN="ghp_your_github_token"
OPENAI_API_KEY="sk-proj-your_openai_key"
```

### Docker Integration
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy provider configurations
COPY providers/ ./providers/

# Set environment
ENV SMART_API_INTEGRATIONS_PROVIDERS_DIR="/app/providers"

COPY . .
CMD ["python", "app.py"]
```

## 📚 Best Practices

1. **Environment Variables**: Always use environment variables for sensitive data
2. **Rate Limiting**: Configure appropriate rate limits for each provider
3. **Error Handling**: Always check `response.success` before using `response.data`
4. **Documentation**: Document your custom endpoints clearly
5. **Testing**: Test your integration thoroughly before production
6. **Monitoring**: Log API calls and monitor rate limits

## 🤝 Contributing

Want to add support for a popular API? Contributions are welcome!

1. Fork the repository
2. Add your provider configuration
3. Test thoroughly
4. Submit a pull request

## 📞 Support

- GitHub Issues: Report bugs and feature requests
- Documentation: Full API reference available
- Examples: Check the `examples/` directory for more use cases

---

**Ready to integrate any API in minutes? Install `smart-api-integrations` and start building!** 🚀 