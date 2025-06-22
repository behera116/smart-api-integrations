# 🪝 Webhook Handler Guide

## 🎯 Overview

This guide shows you how to create, customize, and manage webhook handlers using Smart API Integrations. Transform webhook handling from repetitive boilerplate to standardized, type-safe event processing.

## 🚀 Quick Start

### 1. Add Webhook Configuration

```bash
# Add webhook configuration to a provider
smart-api-integrations add-webhook github --event push --secret-env GITHUB_WEBHOOK_SECRET
```

This creates `providers/github/webhook.yaml`:

```yaml
webhooks:
  default:
    path: /webhooks/github
    verify_signature: true
    signing_secret_env: GITHUB_WEBHOOK_SECRET
    verification_type: hmac_sha256
    signature_header: X-Hub-Signature-256
    event_header: X-GitHub-Event
    events:
      - push
```

### 2. Generate Handler Class

```bash
# Generate a webhook handler class
smart-api-integrations generate-webhook-handler github \
    --events push pull_request \
    --output-file ./handlers/github_handler.py
```

### 3. Implement Your Handler

```python
# handlers/github_handler.py (generated)
from smart_api_integrations.webhooks import generate_webhook_handler

GitHubHandler = generate_webhook_handler('github', events=['push', 'pull_request'])

class MyGitHubHandler(GitHubHandler):
    def on_push(self, event):
        """Handle GitHub push events."""
        repo_name = event.payload['repository']['name']
        commits = event.payload['commits']
        
        print(f"Push to {repo_name}: {len(commits)} commits")
        
        # Your business logic here
        self.process_commits(commits)
        
        return self.success_response({
            'processed': True,
            'commits_count': len(commits)
        })
    
    def on_pull_request(self, event):
        """Handle GitHub pull request events."""
        action = event.payload['action']
        pr_number = event.payload['pull_request']['number']
        
        if action == 'opened':
            self.handle_pr_opened(event.payload)
        elif action == 'closed':
            self.handle_pr_closed(event.payload)
        
        return self.success_response({'action': action, 'pr': pr_number})
    
    def process_commits(self, commits):
        """Custom business logic for processing commits."""
        for commit in commits:
            print(f"Commit: {commit['message']}")
    
    def handle_pr_opened(self, payload):
        """Handle PR opened events."""
        # Add your logic here
        pass
    
    def handle_pr_closed(self, payload):
        """Handle PR closed events."""
        # Add your logic here
        pass
```

### 4. Integrate with Framework

```python
# app.py
from flask import Flask
from smart_api_integrations.frameworks.flask import get_webhook_routes
from handlers.github_handler import MyGitHubHandler

app = Flask(__name__)

# Register webhook routes
app.register_blueprint(get_webhook_routes('flask', {
    'github': MyGitHubHandler()
}))

if __name__ == '__main__':
    app.run(debug=True)
```

## 🔧 Configuration Options

### Basic Configuration

```yaml
# providers/myapi/webhook.yaml
webhooks:
  default:
    path: /webhooks/myapi
    verify_signature: true
    signing_secret_env: MYAPI_WEBHOOK_SECRET
    verification_type: hmac_sha256
    signature_header: X-MyAPI-Signature
    event_header: X-MyAPI-Event
    events:
      - user.created
      - user.updated
      - order.completed
```

### Advanced Configuration

```yaml
webhooks:
  # Main webhook endpoint
  default:
    path: /webhooks/myapi
    verify_signature: true
    signing_secret_env: MYAPI_WEBHOOK_SECRET
    verification_type: hmac_sha256
    signature_header: X-MyAPI-Signature
    event_header: X-MyAPI-Event
    events:
      - user.created
      - user.updated
    
  # Separate endpoint for orders
  orders:
    path: /webhooks/myapi/orders
    verify_signature: true
    signing_secret_env: MYAPI_ORDERS_SECRET
    verification_type: hmac_sha1
    signature_header: X-Orders-Signature
    event_header: X-Order-Event
    events:
      - order.created
      - order.completed
      - order.cancelled
    
  # Public endpoint (no signature verification)
  public:
    path: /webhooks/myapi/public
    verify_signature: false
    events:
      - ping
      - health_check
```

### Verification Types

| Type | Description | Example Providers |
|------|-------------|-------------------|
| `hmac_sha256` | HMAC with SHA-256 | GitHub, Stripe |
| `hmac_sha1` | HMAC with SHA-1 | PayPal, older APIs |
| `jwt` | JWT token verification | Auth0, Firebase |
| `custom` | Custom verification logic | Provider-specific |

## 🎭 Handler Classes

### Generated Handler Structure

```python
# Auto-generated base handler
class GitHubHandler:
    def __init__(self):
        self.provider = 'github'
        self.config = load_webhook_config('github')
    
    def handle_webhook(self, request):
        """Main webhook handling method."""
        # 1. Verify signature
        # 2. Extract event type
        # 3. Route to appropriate method
        # 4. Return response
    
    def on_push(self, event):
        """Override this method to handle push events."""
        return self.success_response()
    
    def on_pull_request(self, event):
        """Override this method to handle pull request events."""
        return self.success_response()
    
    def success_response(self, data=None):
        """Return standardized success response."""
        return {'status': 'success', 'data': data or {}}
    
    def error_response(self, message, status_code=400):
        """Return standardized error response."""
        return {'status': 'error', 'message': message}, status_code
```

### Custom Handler Implementation

```python
from smart_api_integrations.webhooks import generate_webhook_handler
import logging

# Generate base handler
StripeHandler = generate_webhook_handler('stripe', events=[
    'payment_intent.succeeded',
    'payment_intent.payment_failed',
    'customer.created',
    'invoice.payment_succeeded'
])

class MyStripeHandler(StripeHandler):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
    
    def on_payment_intent_succeeded(self, event):
        """Handle successful payments."""
        payment_intent = event.payload['data']['object']
        amount = payment_intent['amount']
        customer_id = payment_intent['customer']
        
        self.logger.info(f"Payment succeeded: ${amount/100} for customer {customer_id}")
        
        # Process successful payment
        self.fulfill_order(payment_intent)
        self.send_confirmation_email(customer_id)
        
        return self.success_response({
            'payment_processed': True,
            'amount': amount,
            'customer': customer_id
        })
    
    def on_payment_intent_payment_failed(self, event):
        """Handle failed payments."""
        payment_intent = event.payload['data']['object']
        failure_reason = payment_intent.get('last_payment_error', {}).get('message')
        
        self.logger.warning(f"Payment failed: {failure_reason}")
        
        # Handle failed payment
        self.notify_payment_failure(payment_intent)
        
        return self.success_response({
            'payment_failed': True,
            'reason': failure_reason
        })
    
    def fulfill_order(self, payment_intent):
        """Custom business logic for order fulfillment."""
        # Your implementation here
        pass
    
    def send_confirmation_email(self, customer_id):
        """Send confirmation email to customer."""
        # Your implementation here
        pass
    
    def notify_payment_failure(self, payment_intent):
        """Notify about payment failure."""
        # Your implementation here
        pass
```

## 🧪 Testing Webhooks

### 1. CLI Testing

```bash
# Test webhook handler with sample payload
smart-api-integrations test-webhook github push

# Test specific event
smart-api-integrations test-webhook stripe payment_intent.succeeded

# Test with custom payload
smart-api-integrations test-webhook github push --payload-file ./test_data/github_push.json
```

### 2. Unit Testing

```python
# test_webhooks.py
import json
import pytest
from handlers.github_handler import MyGitHubHandler
from smart_api_integrations.webhooks.base import WebhookEvent

class TestGitHubHandler:
    def setup_method(self):
        self.handler = MyGitHubHandler()
    
    def test_push_event(self):
        # Load test payload
        with open('test_data/github_push.json') as f:
            payload = json.load(f)
        
        # Create webhook event
        event = WebhookEvent(
            provider='github',
            event_type='push',
            payload=payload,
            headers={'X-GitHub-Event': 'push'}
        )
        
        # Test handler
        response = self.handler.on_push(event)
        
        # Assertions
        assert response['status'] == 'success'
        assert response['data']['processed'] == True
        assert 'commits_count' in response['data']
    
    def test_pull_request_opened(self):
        payload = {
            'action': 'opened',
            'pull_request': {'number': 123, 'title': 'Test PR'}
        }
        
        event = WebhookEvent(
            provider='github',
            event_type='pull_request',
            payload=payload,
            headers={'X-GitHub-Event': 'pull_request'}
        )
        
        response = self.handler.on_pull_request(event)
        
        assert response['status'] == 'success'
        assert response['data']['action'] == 'opened'
        assert response['data']['pr'] == 123
```

### 3. Integration Testing

```python
# test_webhook_integration.py
import json
from flask import Flask
from smart_api_integrations.frameworks.flask import get_webhook_routes
from handlers.github_handler import MyGitHubHandler

def test_webhook_endpoint():
    app = Flask(__name__)
    app.register_blueprint(get_webhook_routes('flask', {
        'github': MyGitHubHandler()
    }))
    
    client = app.test_client()
    
    # Test webhook endpoint
    payload = {'repository': {'name': 'test-repo'}, 'commits': []}
    headers = {
        'X-GitHub-Event': 'push',
        'X-Hub-Signature-256': 'sha256=...'  # Calculate proper signature
    }
    
    response = client.post('/webhooks/github', 
                          json=payload, 
                          headers=headers)
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
```

## 🔐 Security Best Practices

### 1. Signature Verification

```python
# Always verify webhook signatures
class SecureHandler(BaseHandler):
    def handle_webhook(self, request):
        # Signature verification is automatic, but you can add extra checks
        if not self.verify_timestamp(request):
            return self.error_response('Request too old', 401)
        
        return super().handle_webhook(request)
    
    def verify_timestamp(self, request):
        """Verify request timestamp to prevent replay attacks."""
        timestamp = request.headers.get('X-Timestamp')
        if not timestamp:
            return False
        
        import time
        current_time = int(time.time())
        request_time = int(timestamp)
        
        # Reject requests older than 5 minutes
        return abs(current_time - request_time) < 300
```

### 2. Environment Variables

```bash
# Use strong, unique secrets for each provider
export GITHUB_WEBHOOK_SECRET="your_github_webhook_secret_here"
export STRIPE_WEBHOOK_SECRET="whsec_your_stripe_webhook_secret"
export SLACK_WEBHOOK_SECRET="your_slack_webhook_secret"
```

### 3. Rate Limiting

```python
from functools import wraps
import time

def rate_limit(max_calls=100, window=3600):
    """Rate limiting decorator for webhook handlers."""
    calls = {}
    
    def decorator(func):
        @wraps(func)
        def wrapper(self, event):
            now = time.time()
            provider = event.provider
            
            # Clean old entries
            calls[provider] = [t for t in calls.get(provider, []) if now - t < window]
            
            # Check rate limit
            if len(calls[provider]) >= max_calls:
                return self.error_response('Rate limit exceeded', 429)
            
            # Record this call
            calls[provider].append(now)
            
            return func(self, event)
        return wrapper
    return decorator

class RateLimitedHandler(BaseHandler):
    @rate_limit(max_calls=50, window=3600)  # 50 calls per hour
    def on_push(self, event):
        return super().on_push(event)
```

## 🚀 Advanced Patterns

### 1. Multi-Provider Handler

```python
class UnifiedWebhookHandler:
    def __init__(self):
        self.github_handler = MyGitHubHandler()
        self.stripe_handler = MyStripeHandler()
        self.slack_handler = MySlackHandler()
    
    def handle_code_changes(self, github_event):
        """Handle code changes across all systems."""
        # Process GitHub push
        result = self.github_handler.on_push(github_event)
        
        # Notify team on Slack
        self.slack_handler.notify_team(f"Code pushed to {github_event.payload['repository']['name']}")
        
        # Update billing if needed
        if self.should_update_billing(github_event):
            self.stripe_handler.update_usage_metrics(github_event)
        
        return result
```

### 2. Event Pipeline

```python
class EventPipeline:
    def __init__(self):
        self.processors = []
        self.filters = []
    
    def add_processor(self, processor):
        self.processors.append(processor)
    
    def add_filter(self, filter_func):
        self.filters.append(filter_func)
    
    def process_event(self, event):
        # Apply filters
        for filter_func in self.filters:
            if not filter_func(event):
                return self.success_response({'filtered': True})
        
        # Process through pipeline
        for processor in self.processors:
            result = processor(event)
            if not result.get('success'):
                return result
        
        return self.success_response({'processed': True})

# Usage
pipeline = EventPipeline()
pipeline.add_filter(lambda e: e.payload.get('repository', {}).get('private') == False)
pipeline.add_processor(lambda e: self.validate_event(e))
pipeline.add_processor(lambda e: self.transform_data(e))
pipeline.add_processor(lambda e: self.store_event(e))
```

## 📚 Next Steps

- **[Framework Integration](framework-integration-guide.md)** - Integrate with Flask, FastAPI, Django
- **[Real Examples](examples/README.md)** - Complete working examples
- **[CLI Reference](cli-reference.md)** - All webhook CLI commands
- **[Best Practices](best-practices.md)** - Production deployment tips 