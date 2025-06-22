# Smart API Webhooks

This module provides a simple yet powerful system for integrating webhooks into your existing applications.

## Quick Start

### 1. Add Webhook Configuration

```bash
smart-api-integrations add-webhook github --event push --secret-env GITHUB_WEBHOOK_SECRET
```

### 2. Create a Provider-Specific Handler Class

```python
from smart_api_integrations.webhooks import generate_webhook_handler

# Generate a webhook handler class for GitHub
GitHubHandler = generate_webhook_handler(
    'github', 
    events=['push', 'pull_request']
)

# Extend with custom logic
class MyGitHubHandler(GitHubHandler):
    def on_push(self, event):
        # Custom push handling
        repo = event.payload['repository']['name']
        return self.success_response({
            'repo': repo,
            'processed': True
        })

# Instantiate the handler
handler = MyGitHubHandler()
```

### 3. Integrate with Your Framework

```python
# Flask
from flask import Flask
from smart_api_integrations.webhooks import get_webhook_routes

app = Flask(__name__)
webhook_blueprint = get_webhook_routes('flask')
app.register_blueprint(webhook_blueprint)

# FastAPI
from fastapi import FastAPI
from smart_api_integrations.webhooks import get_webhook_routes

app = FastAPI()
webhook_router = get_webhook_routes('fastapi')
app.include_router(webhook_router)

# Django
# In urls.py
from django.urls import path, include
from smart_api_integrations.webhooks import get_webhook_routes

urlpatterns = [
    path('api/', include(get_webhook_routes('django'))),
]
```

## Function-Based Handlers

You can also use function-based handlers if you prefer:

```python
from smart_api_integrations.webhooks import smart_webhook_handler

@smart_webhook_handler('github', 'push')
def handle_push(event):
    # Handle push event
    return {'success': True}
```

## Multiple Webhook Endpoints

You can configure multiple webhook endpoints for different purposes:

```bash
# Default webhook
smart-api-integrations add-webhook github --event push --secret-env GITHUB_WEBHOOK_SECRET

# Specialized webhook for repository events
smart-api-integrations add-webhook github --name repo_events --event push --event pull_request --secret-env GITHUB_REPO_SECRET
```

Then handle them with specific webhook handlers:

```python
# Generate handlers for different webhook endpoints
MainGitHubHandler = generate_webhook_handler('github', ['push'])
RepoGitHubHandler = generate_webhook_handler('github', ['push', 'pull_request'], webhook_name='repo_events')

# Instantiate handlers
main_handler = MainGitHubHandler()
repo_handler = RepoGitHubHandler()
```

Or with function-based handlers:

```python
@smart_webhook_handler('github', 'push')
def handle_push(event):
    # Handle default webhook
    pass

@smart_webhook_handler('github', 'push', 'repo_events')
def handle_repo_push(event):
    # Handle repo_events webhook
    pass
```

## Testing Webhooks

Test your webhook handlers with sample payloads:

```bash
# Test default webhook
smart-api-integrations test-webhook github push

# Test specialized webhook
smart-api-integrations test-webhook github push --webhook-name repo_events
```

## Advanced Features

For more advanced features and detailed documentation, see:

- [Complete Webhook Integration Guide](../../docs/webhook_integration_guide.md)
- [Flask Webhook Example](../../examples/flask_webhook_example.py)
- [GitHub Webhook Example](../../examples/github_webhook_example.py) 