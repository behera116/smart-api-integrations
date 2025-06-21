# Adding a New Webhook to Smart API

This guide walks you through adding webhook support for a new provider or extending existing webhook functionality. The Smart API webhook system provides automatic signature verification, event routing, and standardized handling.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Webhook Configuration](#webhook-configuration)
3. [Implementing Webhook Handlers](#implementing-webhook-handlers)
4. [Security & Verification](#security--verification)
5. [Testing Webhooks](#testing-webhooks)
6. [Advanced Features](#advanced-features)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

## Quick Start

### For a New Provider

1. **Create webhook configuration** (`providers/myapi/webhook.yaml`):

```yaml
webhooks:
  default:
    path: "/api/webhooks/myapi/"
    verify_signature: true
    signing_secret_env: "MYAPI_WEBHOOK_SECRET"
    events:
      - "resource.created"
      - "resource.updated"
      - "resource.deleted"
```

2. **Set environment variable**:

```bash
export MYAPI_WEBHOOK_SECRET="whsec_your_webhook_secret"
```

3. **Create a handler**:

```python
from smart_api_integrations.webhooks import webhook_handler

@webhook_handler('myapi', 'resource.created')
def handle_resource_created(event):
    resource = event.payload['data']
    print(f"New resource created: {resource['id']}")
    return {'processed': True, 'resource_id': resource['id']}
```

4. **Test your webhook**:

```bash
python manage.py test_webhook myapi resource.created
```

## Webhook Configuration

### Basic Configuration

Create `providers/myapi/webhook.yaml`:

```yaml
# Basic webhook configuration
webhooks:
  default:
    path: "/api/webhooks/myapi/"
    verify_signature: true
    signing_secret_env: "MYAPI_WEBHOOK_SECRET"
    events:
      - "event.type.one"
      - "event.type.two"
```

### Advanced Configuration

```yaml
# Advanced webhook configuration with multiple endpoints
webhooks:
  # Main webhook endpoint
  default:
    path: "/api/webhooks/myapi/"
    verify_signature: true
    signing_secret_env: "MYAPI_WEBHOOK_SECRET"
    verification_type: "hmac_sha256"  # or hmac_sha1, rsa, custom
    signature_header: "X-MyAPI-Signature"
    timestamp_header: "X-MyAPI-Timestamp"  # For replay protection
    replay_tolerance: 300  # 5 minutes
    events:
      - "user.created"
      - "user.updated"
      - "user.deleted"
      - "payment.completed"
    rate_limit:
      requests_per_minute: 100
      burst_limit: 20
  
  # Separate endpoint for billing events
  billing:
    path: "/api/webhooks/myapi/billing/"
    verify_signature: true
    signing_secret_env: "MYAPI_BILLING_SECRET"
    events:
      - "invoice.created"
      - "invoice.paid"
      - "subscription.changed"

# Global settings for this provider
default_verification_type: "hmac_sha256"
default_signature_header: "X-MyAPI-Signature"
default_timestamp_header: "X-MyAPI-Timestamp"

# Optional IP whitelist for additional security
ip_whitelist:
  - "192.168.1.100"
  - "10.0.0.0/24"
```

### Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `path` | Webhook endpoint URL path | Required |
| `verify_signature` | Enable signature verification | `true` |
| `signing_secret_env` | Environment variable for signing secret | Required if verify_signature |
| `verification_type` | Type of signature verification | `hmac_sha256` |
| `signature_header` | HTTP header containing signature | `X-Signature` |
| `timestamp_header` | HTTP header containing timestamp | `null` |
| `replay_tolerance` | Seconds to accept old webhooks | `300` |
| `events` | List of event types to handle | `[]` |
| `rate_limit` | Rate limiting configuration | `null` |

## Implementing Webhook Handlers

### Function-Based Handlers

Simple handlers using decorators:

```python
from smart_api_integrations.webhooks import webhook_handler

@webhook_handler('myapi', 'user.created')
def handle_user_created(event):
    """Handle new user creation."""
    user = event.payload['data']['user']
    
    # Your business logic
    create_welcome_package(user['id'])
    send_welcome_email(user['email'])
    
    return {
        'processed': True,
        'user_id': user['id'],
        'welcome_sent': True
    }

@webhook_handler('myapi', 'payment.completed')
def handle_payment_completed(event):
    """Handle successful payment."""
    payment = event.payload['data']['payment']
    
    # Process payment
    order = process_payment(payment['id'], payment['amount'])
    
    return {
        'processed': True,
        'order_id': order.id,
        'payment_id': payment['id']
    }
```

### Class-Based Handlers

For more complex logic with shared functionality:

```python
from smart_api_integrations.webhooks import WebhookHandler
from myapp.models import User, Order
from myapp.services import EmailService, OrderService

class MyAPIWebhookHandler(WebhookHandler):
    """
    Comprehensive webhook handler for MyAPI events.
    """
    provider = 'myapi'
    
    def on_user_created(self, event):
        """Handle user.created events."""
        user_data = event.payload['data']['user']
        
        # Create local user
        user = User.objects.create(
            external_id=user_data['id'],
            email=user_data['email'],
            name=user_data['name']
        )
        
        # Send welcome email
        EmailService.send_welcome(user)
        
        return self.success_response({
            'user_id': user.id,
            'external_id': user_data['id']
        })
    
    def on_user_updated(self, event):
        """Handle user.updated events."""
        user_data = event.payload['data']['user']
        previous = event.payload['data'].get('previous_attributes', {})
        
        # Update local user
        user = User.objects.get(external_id=user_data['id'])
        
        # Check what changed
        if 'email' in previous:
            user.email = user_data['email']
            user.email_verified = False
        
        if 'name' in previous:
            user.name = user_data['name']
        
        user.save()
        
        return self.success_response({
            'user_id': user.id,
            'updated_fields': list(previous.keys())
        })
    
    def on_payment_completed(self, event):
        """Handle payment.completed events."""
        payment = event.payload['data']['payment']
        
        try:
            # Process the payment
            order = OrderService.complete_payment(
                payment_id=payment['id'],
                amount=payment['amount'],
                currency=payment['currency']
            )
            
            return self.success_response({
                'order_id': order.id,
                'payment_id': payment['id'],
                'status': 'completed'
            })
            
        except Order.DoesNotExist:
            return self.error_response(
                'Order not found',
                {'payment_id': payment['id']}
            )

# Initialize the handler (registers all on_* methods)
myapi_handler = MyAPIWebhookHandler()
```

### Batch Event Handlers

Handle multiple event types with one handler:

```python
from smart_api_integrations.webhooks import batch_webhook_handler

@batch_webhook_handler('myapi', [
    'resource.created',
    'resource.updated',
    'resource.deleted'
])
def handle_resource_events(event):
    """Handle all resource-related events."""
    resource = event.payload['data']['resource']
    
    if event.type == 'resource.created':
        return handle_create(resource)
    elif event.type == 'resource.updated':
        return handle_update(resource)
    else:  # deleted
        return handle_delete(resource)
```

### Webhook Middleware

Add preprocessing, logging, or authentication:

```python
from smart_api_integrations.webhooks import webhook_middleware

@webhook_middleware('myapi')
def log_all_events(event):
    """Log all incoming webhook events."""
    logger.info(f"Webhook received: {event.provider} - {event.type}")
    logger.debug(f"Payload: {event.payload}")
    
    # Add processing timestamp
    event.headers['X-Processed-At'] = str(datetime.now())
    
    # Return None to continue processing
    return None

@webhook_middleware('myapi')
def validate_account(event):
    """Validate webhook is for active account."""
    account_id = event.payload.get('account_id')
    
    if not account_id:
        return WebhookResponse(
            success=False,
            status_code=400,
            message="Missing account_id"
        )
    
    account = Account.objects.filter(id=account_id, active=True).first()
    if not account:
        return WebhookResponse(
            success=False,
            status_code=404,
            message="Account not found or inactive"
        )
    
    # Store account in event for handlers
    event.account = account
    return None
```

## Security & Verification

### Built-in Verification Types

#### HMAC SHA256 (Most Common)

```yaml
webhooks:
  default:
    verification_type: "hmac_sha256"
    signature_header: "X-Webhook-Signature"
    signing_secret_env: "WEBHOOK_SECRET"
```

The system automatically verifies:
```
expected = hmac.new(secret, payload, hashlib.sha256).hexdigest()
signature == expected
```

#### Custom Verification

For providers with unique verification methods:

```python
from smart_api_integrations.core.webhook import WebhookVerifier

class MyAPIWebhookVerifier(WebhookVerifier):
    """Custom signature verification for MyAPI."""
    
    def verify(self, payload: bytes, signature: str, secret: str, **kwargs) -> bool:
        """Verify webhook signature using MyAPI's method."""
        # Extract components from signature
        timestamp, hash_value = signature.split(',')
        
        # Check timestamp (prevent replay attacks)
        current_time = int(time.time())
        if abs(current_time - int(timestamp)) > 300:  # 5 minutes
            return False
        
        # Verify signature
        message = f"{timestamp}.{payload.decode('utf-8')}"
        expected = hmac.new(
            secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected, hash_value)

# Register custom verifier
from smart_api_integrations.core.webhook_registry import get_webhook_registry

registry = get_webhook_registry()
processor = registry.create_processor('myapi')
processor.verifier = MyAPIWebhookVerifier()
```

### Replay Attack Protection

Configure timestamp validation:

```yaml
webhooks:
  default:
    timestamp_header: "X-Webhook-Timestamp"
    replay_tolerance: 300  # Accept webhooks up to 5 minutes old
```

### IP Whitelisting

Restrict webhooks to specific IPs:

```yaml
ip_whitelist:
  - "192.168.1.100"     # Single IP
  - "10.0.0.0/24"       # CIDR range
  - "2001:db8::/32"     # IPv6 range
```

## Testing Webhooks

### Using the Test Command

```bash
# Test with auto-generated sample payload
python manage.py test_webhook myapi user.created

# Test with custom payload
python manage.py test_webhook myapi payment.completed \
  --payload '{
    "data": {
      "payment": {
        "id": "pay_123",
        "amount": 2000,
        "currency": "usd"
      }
    }
  }'

# Test with payload from file
python manage.py test_webhook myapi user.updated \
  --payload-file tests/fixtures/user_updated.json

# List all registered handlers
python manage.py test_webhook myapi user.created --list-handlers

# Generate sample payload
python manage.py test_webhook myapi resource.created --sample-payload
```

### Creating Test Fixtures

Create `tests/fixtures/myapi_webhooks.json`:

```json
{
  "user.created": {
    "id": "evt_test_123",
    "type": "user.created",
    "data": {
      "user": {
        "id": "usr_123",
        "email": "test@example.com",
        "name": "Test User",
        "created_at": "2024-01-01T00:00:00Z"
      }
    },
    "account_id": "acc_123"
  },
  "payment.completed": {
    "id": "evt_test_456",
    "type": "payment.completed",
    "data": {
      "payment": {
        "id": "pay_123",
        "amount": 2000,
        "currency": "usd",
        "status": "completed",
        "metadata": {
          "order_id": "ord_123"
        }
      }
    },
    "account_id": "acc_123"
  }
}
```

### Unit Testing Handlers

```python
import pytest
from unittest.mock import patch
from smart_api_integrations.core.webhook_schema import WebhookEvent
from smart_api_integrations.webhooks.handlers import MyAPIWebhookHandler

class TestMyAPIWebhooks:
    @pytest.fixture
    def handler(self):
        return MyAPIWebhookHandler()
    
    @pytest.fixture
    def user_created_event(self):
        return WebhookEvent(
            id="evt_test_123",
            type="user.created",
            provider="myapi",
            webhook_name="default",
            payload={
                "data": {
                    "user": {
                        "id": "usr_123",
                        "email": "test@example.com",
                        "name": "Test User"
                    }
                }
            },
            headers={},
            timestamp=datetime.now(timezone.utc),
            verified=True
        )
    
    def test_user_created_handler(self, handler, user_created_event):
        """Test user creation handler."""
        with patch('myapp.models.User.objects.create') as mock_create:
            mock_user = Mock(id=1, external_id="usr_123")
            mock_create.return_value = mock_user
            
            response = handler.on_user_created(user_created_event)
            
            assert response['success'] is True
            assert response['data']['external_id'] == "usr_123"
            mock_create.assert_called_once()
    
    def test_payment_completed_handler(self, handler):
        """Test payment completion handler."""
        event = WebhookEvent(
            id="evt_test_456",
            type="payment.completed",
            provider="myapi",
            webhook_name="default",
            payload={
                "data": {
                    "payment": {
                        "id": "pay_123",
                        "amount": 2000,
                        "currency": "usd"
                    }
                }
            },
            headers={},
            timestamp=datetime.now(timezone.utc),
            verified=True
        )
        
        with patch('myapp.services.OrderService.complete_payment') as mock_complete:
            mock_order = Mock(id=1)
            mock_complete.return_value = mock_order
            
            response = handler.on_payment_completed(event)
            
            assert response['success'] is True
            assert response['data']['payment_id'] == "pay_123"
```

### Integration Testing

```python
import json
from django.test import TestCase, Client
from django.urls import reverse

class TestWebhookIntegration(TestCase):
    def setUp(self):
        self.client = Client()
        self.webhook_url = reverse('smart_api_integrations:webhook-default', kwargs={
            'provider': 'myapi'
        })
        
        # Set up test data
        self.webhook_payload = {
            'event_type': 'resource.created',
            'data': {
                'id': '123',
                'name': 'Test Resource'
            }
        }
    
    def test_webhook_endpoint(self):
        """Test webhook endpoint accepts valid webhooks."""
        payload = {
            "id": "evt_123",
            "type": "user.created",
            "data": {
                "user": {
                    "id": "usr_123",
                    "email": "test@example.com"
                }
            }
        }
        
        # Create signature (simplified for testing)
        import hmac
        import hashlib
        secret = "test_secret"
        signature = hmac.new(
            secret.encode(),
            json.dumps(payload).encode(),
            hashlib.sha256
        ).hexdigest()
        
        response = self.client.post(
            self.webhook_url,
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_WEBHOOK_SIGNATURE=signature
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
```

## Advanced Features

### Async Processing

For heavy processing, queue events:

```python
from celery import shared_task
from smart_api_integrations.webhooks import webhook_handler

@webhook_handler('myapi', 'large.import')
def handle_large_import(event):
    """Queue large import for async processing."""
    import_id = event.payload['data']['import_id']
    
    # Queue for async processing
    process_import.delay(import_id, event.payload)
    
    return {
        'queued': True,
        'import_id': import_id,
        'message': 'Import queued for processing'
    }

@shared_task
def process_import(import_id, payload):
    """Process import asynchronously."""
    # Heavy processing here
    pass
```

### Conditional Handlers

Handle events based on conditions:

```python
@webhook_handler('myapi', 'order.updated')
def handle_order_updated(event):
    """Handle order updates with conditions."""
    order = event.payload['data']['order']
    previous = event.payload['data'].get('previous_attributes', {})
    
    # Only process if status changed
    if 'status' not in previous:
        return {'processed': False, 'reason': 'Status unchanged'}
    
    old_status = previous['status']
    new_status = order['status']
    
    # Handle specific transitions
    if old_status == 'pending' and new_status == 'paid':
        return process_payment_confirmation(order)
    elif old_status == 'paid' and new_status == 'shipped':
        return send_shipping_notification(order)
    elif new_status == 'cancelled':
        return process_cancellation(order)
    
    return {'processed': True, 'transition': f"{old_status} -> {new_status}"}
```

### Event Transformation

Transform events before processing:

```python
@webhook_middleware('myapi')
def transform_legacy_events(event):
    """Transform legacy event format to new format."""
    if event.type.startswith('legacy.'):
        # Transform legacy events
        event.type = event.type.replace('legacy.', '')
        
        # Transform payload structure
        if 'old_data' in event.payload:
            event.payload['data'] = transform_legacy_data(event.payload['old_data'])
            del event.payload['old_data']
    
    return None  # Continue processing
```

### Multi-tenant Webhooks

Handle webhooks for multiple accounts:

```python
class MultiTenantWebhookHandler(WebhookHandler):
    provider = 'myapi'
    webhook_name = 'multi_tenant'
    
    def get_account(self, event):
        """Get account from webhook payload."""
        account_id = event.payload.get('account_id')
        if not account_id:
            raise ValueError("Missing account_id in webhook")
        
        return Account.objects.get(external_id=account_id)
    
    def on_resource_created(self, event):
        """Handle resource creation for specific account."""
        account = self.get_account(event)
        resource_data = event.payload['data']['resource']
        
        # Create resource for specific account
        resource = Resource.objects.create(
            account=account,
            external_id=resource_data['id'],
            name=resource_data['name']
        )
        
        return self.success_response({
            'resource_id': resource.id,
            'account_id': account.id
        })
```

## Best Practices

### 1. Idempotency

Make handlers idempotent to handle duplicate webhooks:

```python
@webhook_handler('myapi', 'payment.completed')
def handle_payment_completed(event):
    payment_id = event.payload['data']['payment']['id']
    
    # Check if already processed
    if Payment.objects.filter(external_id=payment_id).exists():
        return {
            'processed': False,
            'reason': 'Payment already processed',
            'payment_id': payment_id
        }
    
    # Process payment
    payment = Payment.objects.create(
        external_id=payment_id,
        amount=event.payload['data']['payment']['amount']
    )
    
    return {'processed': True, 'payment_id': payment.id}
```

### 2. Error Handling

Handle errors gracefully:

```python
class RobustWebhookHandler(WebhookHandler):
    provider = 'myapi'
    
    def on_user_created(self, event):
        try:
            user_data = event.payload['data']['user']
            user = self.create_user(user_data)
            return self.success_response({'user_id': user.id})
            
        except KeyError as e:
            logger.error(f"Missing required field: {e}")
            return self.error_response(
                f"Missing required field: {e}",
                {'event_id': event.id}
            )
            
        except IntegrityError as e:
            logger.warning(f"User already exists: {e}")
            return self.success_response({
                'processed': False,
                'reason': 'User already exists'
            })
            
        except Exception as e:
            logger.exception(f"Unexpected error processing webhook: {e}")
            return self.webhook_response(
                success=False,
                status_code=500,
                message="Internal server error"
            )
```

### 3. Logging

Comprehensive logging for debugging:

```python
import structlog

logger = structlog.get_logger()

@webhook_handler('myapi', 'important.event')
def handle_important_event(event):
    log = logger.bind(
        event_id=event.id,
        event_type=event.type,
        provider=event.provider
    )
    
    log.info("Processing webhook event")
    
    try:
        result = process_event(event.payload)
        log.info("Event processed successfully", result=result)
        return {'processed': True, 'result': result}
        
    except Exception as e:
        log.error("Failed to process event", error=str(e), exc_info=True)
        raise
```

### 4. Performance

Optimize for performance:

```python
@webhook_handler('myapi', 'bulk.update')
def handle_bulk_update(event):
    """Handle bulk updates efficiently."""
    updates = event.payload['data']['updates']
    
    # Use bulk operations
    resources = []
    for update in updates:
        resources.append(Resource(
            external_id=update['id'],
            name=update['name'],
            status=update['status']
        ))
    
    # Bulk create/update
    Resource.objects.bulk_create(
        resources,
        update_conflicts=True,
        update_fields=['name', 'status']
    )
    
    return {
        'processed': True,
        'count': len(resources)
    }
```

### 5. Security

Always validate and sanitize input:

```python
@webhook_handler('myapi', 'user.input')
def handle_user_input(event):
    """Handle user input with validation."""
    from django.core.validators import validate_email
    
    user_data = event.payload['data']['user']
    
    # Validate email
    try:
        validate_email(user_data['email'])
    except ValidationError:
        return {
            'processed': False,
            'error': 'Invalid email address'
        }
    
    # Sanitize input
    user_data['name'] = bleach.clean(user_data['name'])
    
    # Process safely
    user = create_user(user_data)
    return {'processed': True, 'user_id': user.id}
```

## Troubleshooting

### Webhook Not Triggering

1. **Check registration**:
```bash
python manage.py test_webhook myapi user.created --list-handlers
```

2. **Verify configuration**:
```bash
cat providers/myapi/webhook.yaml
```

3. **Check imports**:
```python
# Ensure handlers are imported at startup
# In your app's __init__.py or apps.py:
from . import webhooks  # Import webhook handlers
```

### Signature Verification Failing

1. **Check environment variable**:
```bash
echo $MYAPI_WEBHOOK_SECRET
```

2. **Verify signature format**:
```python
# Add debug logging
@webhook_handler('myapi', 'test.event')
def debug_webhook(event):
    print(f"Headers: {event.headers}")
    print(f"Signature: {event.headers.get('HTTP_X_WEBHOOK_SIGNATURE')}")
    return {'debug': True}
```

3. **Test manually**:
```python
import hmac
import hashlib

secret = "your_secret"
payload = '{"test": "data"}'
signature = hmac.new(
    secret.encode(),
    payload.encode(),
    hashlib.sha256
).hexdigest()
print(f"Expected signature: {signature}")
```

### Handler Not Found

1. **Check event type matching**:
```python
# Ensure event types match exactly
@webhook_handler('myapi', 'user.created')  # Must match webhook event type
```

2. **Verify handler registration**:
```python
from smart_api_integrations.core.webhook_registry import get_webhook_registry

registry = get_webhook_registry()
processor = registry.get_processor('myapi:default')
print(f"Registered handlers: {list(processor.handlers.keys())}")
```

### Performance Issues

1. **Use async processing**:
```python
@webhook_handler('myapi', 'heavy.task')
def queue_heavy_task(event):
    task_id = queue_task.delay(event.payload)
    return {'queued': True, 'task_id': str(task_id)}
```

2. **Optimize database queries**:
```python
# Use select_related and prefetch_related
resources = Resource.objects.select_related('category').filter(
    external_id__in=[r['id'] for r in event.payload['resources']]
)
```

3. **Implement caching**:
```python
from django.core.cache import cache

@webhook_handler('myapi', 'frequent.event')
def handle_with_cache(event):
    cache_key = f"webhook:{event.type}:{event.id}"
    
    # Check cache
    result = cache.get(cache_key)
    if result:
        return result
    
    # Process and cache
    result = process_event(event)
    cache.set(cache_key, result, 3600)  # Cache for 1 hour
    return result
```

## Next Steps

1. **Monitor Webhooks**: Set up monitoring and alerting for webhook failures
2. **Add Metrics**: Track webhook processing times and success rates
3. **Document Events**: Create documentation for all webhook events your app handles
4. **Test End-to-End**: Test the complete webhook flow from provider to your handlers

For more examples, see the existing webhook implementations in `src/webhooks/` directory.