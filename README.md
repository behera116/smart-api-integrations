# 🚀 Smart API Integrations

**Connect to any API and receive webhooks with minimal code.**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## What This Package Does

Smart API Integrations eliminates boilerplate code for:

1. **API Integration** - Connect to third-party APIs with simple function calls
2. **Webhook Handling** - Process incoming events from external services

## Before vs After

### API Integration

**Before Smart API Integrations:**
```python
import requests
import os

# Set up authentication
token = os.environ.get("GITHUB_TOKEN")
headers = {"Authorization": f"Bearer {token}"}

# Make the request
response = requests.get("https://api.github.com/users/octocat", headers=headers)

# Handle the response
if response.status_code == 200:
    user = response.json()
    print(f"User: {user['name']}")
else:
    print(f"Error: {response.status_code}")
    print(response.text)
```

**After Smart API Integrations:**
```python
from smart_api_integrations import GithubAPIClient

# Create client (automatically uses GITHUB_TOKEN from environment)
github = GithubAPIClient()

# Make the request
user = github.get_user(username='octocat')
print(f"User: {user.data['name']}")
```

### Webhook Handling

**Before Smart API Integrations:**
```python
from flask import Flask, request, jsonify
import hmac
import hashlib
import os

app = Flask(__name__)

@app.route('/webhooks/stripe', methods=['POST'])
def stripe_webhook():
    # Verify signature
    signature = request.headers.get('Stripe-Signature')
    secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    if not signature or not secret:
        return jsonify({"error": "Missing signature"}), 400
        
    # Compute expected signature
    payload = request.data
    expected_sig = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    # Verify signature
    if not hmac.compare_digest(expected_sig, signature):
        return jsonify({"error": "Invalid signature"}), 401
    
    # Process the event
    event_data = request.json
    event_type = event_data.get('type')
    
    if event_type == 'payment_intent.succeeded':
        # Handle payment success
        amount = event_data['data']['object']['amount'] / 100
        print(f"Payment received: ${amount}")
    elif event_type == 'payment_intent.payment_failed':
        # Handle payment failure
        print("Payment failed")
    
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(port=5000)
```

**After Smart API Integrations:**
```python
from flask import Flask
from smart_api_integrations.webhooks import smart_webhook_handler
from smart_api_integrations.frameworks.flask import register_webhook_routes

app = Flask(__name__)

@smart_webhook_handler('stripe', 'payment_intent.succeeded')
def handle_payment(event):
    amount = event.payload['data']['object']['amount'] / 100
    print(f"Payment received: ${amount}")
    return {"status": "processed"}

@smart_webhook_handler('stripe', 'payment_intent.payment_failed')
def handle_payment_failure(event):
    print("Payment failed")
    return {"status": "handled"}

# Register all webhook routes
register_webhook_routes(app)

if __name__ == '__main__':
    app.run(port=5000)
```

## 🚀 Quick Start

### Installation

```bash
pip install smart-api-integrations
```

### API Integration

```python
from smart_api_integrations import UniversalAPIClient

# Create a client for any configured API provider
github = UniversalAPIClient('github')  # Uses GITHUB_TOKEN from environment

# Call methods based on the provider's configuration
user = github.get_user(username='octocat')
print(f"User: {user.data['name']}")
```

### Webhook Integration

```python
from smart_api_integrations.webhooks import smart_webhook_handler

@smart_webhook_handler('stripe', 'payment_intent.succeeded')
def handle_payment(event):
    amount = event.payload['data']['object']['amount'] / 100
    print(f"Payment received: ${amount}")
    return {"status": "processed"}
```

## 📚 Documentation

### Getting Started
- [Quick Start Guide](docs/quick-start-guide.md)
- [API Client Guide](docs/api-client-guide.md)
- [Webhook Integration](docs/webhook_integration.md)

### API Integration
- [Adding New Providers](docs/adding-new-providers.md)
- [OpenAPI Integration](docs/openapi_integration.md)
- [Type Safety Guide](docs/type-safety-guide.md)

### Webhook Integration
- [Webhook System Overview](docs/webhook-system-overview.md)
- [Webhook Handler Guide](docs/webhook-handler-guide.md)
- [Framework Integration Guide](docs/framework-integration-guide.md)

### Reference
- [CLI Reference](docs/cli-reference.md)
- [Provider Configuration Guide](docs/provider-priority-guide.md)
- [Package Setup Guide](docs/package-setup-guide.md)

### Examples
- [API Examples](examples/github_basic_example.py)
- [Webhook Examples](examples/webhook_integration_example.py)
- [Framework Examples](examples/flask_webhook_example.py)

## 🔧 Key Features

- ✅ **Zero Boilerplate**: Define endpoints once, use everywhere
- ✅ **Type Safety**: Full IDE support with generated type stubs
- ✅ **Smart Parameters**: Automatic handling of path/query/body parameters
- ✅ **Framework Integration**: Works with Flask, FastAPI, and Django
- ✅ **Webhook Support**: Easily handle incoming webhook events
- ✅ **OpenAPI Support**: Generate clients from API documentation

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

**Stop writing API boilerplate. Start building features.** 🚀
