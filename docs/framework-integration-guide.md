# Webhook Integration Guide

Smart API Integrations provides a powerful webhook system that allows you to easily handle incoming webhook events from various providers.

| Framework | Integration | Example |
|-----------|------------|---------|
| Flask | `init_flask_app(app)` | [Flask Example](../examples/flask_webhook_example.py) |
| FastAPI | `init_fastapi_app(app)` | [FastAPI Integration](../src/frameworks/fastapi.py) |
| Django | `path('api/', include(get_webhook_urls()))` | [Django Integration](../src/frameworks/django.py) |

| Provider | Example Handler | Configuration |
|----------|----------------|---------------|
| GitHub | [GitHub Handler](../examples/github_webhook_example.py) | [GitHub Webhook Config](../providers/github/webhook.yaml) |
| Stripe | [Stripe Handler](../src/webhooks/stripe.py) | `add-webhook stripe --event payment_intent.succeeded` |

## Adding Webhook Configuration

To add webhook configuration to a provider:

```bash
smart-api-integrations add-webhook github --event push --secret-env GITHUB_WEBHOOK_SECRET
```

This creates a `webhook.yaml` file in the provider's directory.

### Example Configuration

```yaml
webhooks:
  default:
    path: /webhooks/github
    verify_signature: true
    signing_secret_env: GITHUB_WEBHOOK_SECRET
    verification_type: hmac_sha256
    signature_header: X-Hub-Signature-256
    events:
      - push
      - pull_request
```

## Creating Webhook Handlers

```python
from smart_api_integrations.webhooks import smart_webhook_handler

@smart_webhook_handler('github', 'push')
def handle_github_push(event):
    """Handle GitHub push events."""
    repo = event.payload['repository']['name']
    commits = event.payload['commits']
    
    return {
        'success': True,
        'message': 'Push event processed',
        'data': {
            'repo': repo,
            'commits_count': len(commits)
        }
    }
```

## Framework Integration

### Flask

```python
from flask import Flask
from smart_api_integrations.frameworks.flask import init_flask_app

app = Flask(__name__)
init_flask_app(app)
```

### FastAPI

```python
from fastapi import FastAPI
from smart_api_integrations.frameworks.fastapi import init_fastapi_app

app = FastAPI()
init_fastapi_app(app)
```

### Django

```python
# In urls.py
from django.urls import path, include
from smart_api_integrations.frameworks.django import get_webhook_urls

urlpatterns = [
    path('api/', include(get_webhook_urls())),
]
```

## Testing Webhooks

Test your webhook handlers:

```bash
smart-api-integrations test-webhook github push
``` 