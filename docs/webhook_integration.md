# Webhook Integration Made Simple

This guide will help you set up webhooks to receive real-time notifications from services like Stripe, GitHub, or Slack.

## What Are Webhooks?

Think of webhooks as "phone calls" from other services to your application:

1. You register your phone number (URL) with a service
2. When something happens (like a payment), the service calls your number
3. Your application answers the call and takes action

For example, when a customer makes a payment on Stripe:
- Stripe calls your webhook URL
- Your application receives the payment details
- You can mark the order as paid, send confirmation emails, etc.

## How Our Library Makes Webhooks Easy

Without this library, you'd need to:
- Create secure endpoints
- Verify webhook signatures (to prevent fake requests)
- Parse different data formats
- Route events to the right code

Our webhook system handles all of this for you:
1. Creates secure URLs for each service
2. Verifies that requests are legitimate
3. Converts data to a standard format
4. Sends each event to your specific handler function
5. Returns proper responses

## Setting Up Webhooks in 3 Steps

### Step 1: Create a Simple Configuration File

Create a `webhook.yaml` file that tells the system how to handle webhooks from a service:

```yaml
# providers/stripe/webhook.yaml (simple version)
webhooks:
  default:
    path: /webhooks/stripe/
    verify_signature: true
    signing_secret_env: STRIPE_WEBHOOK_SECRET
```

This tells the system:
- Create a URL at `/webhooks/stripe/`
- Check that webhooks are legitimate using a signature
- Get the secret key from the STRIPE_WEBHOOK_SECRET environment variable

For more advanced needs, you can add these optional settings:

```yaml
# Advanced settings (optional)
webhooks:
  default:
    # ... basic settings from above ...
    signature_header: Stripe-Signature  # Header containing the signature
    events:                             # Events you expect to receive
      - payment.succeeded
      - payment.failed
    rate_limit:                         # Prevent overload
      requests_per_minute: 60
```

### Step 2: Set Your Secret Key

Set the environment variable with the secret key from your service provider:

```bash
# For Stripe
export STRIPE_WEBHOOK_SECRET=whsec_your_webhook_signing_secret

# For GitHub
export GITHUB_WEBHOOK_SECRET=your_github_webhook_secret
```

You can find this secret in your service provider's dashboard (e.g., Stripe Dashboard → Developers → Webhooks).

### Step 3: Write Your Event Handlers

Create a file with functions that will run when specific events happen:

```python
# webhook_handlers.py
from smart_api_integrations.core.webhook_registry import get_webhook_registry

# Connect to the webhook system
registry = get_webhook_registry()
processor = registry.create_processor("stripe", "default")

# This function runs when a payment succeeds
@processor.on("payment.succeeded")
def handle_payment_succeeded(event):
    # Get the payment details from the event
    payment_data = event.payload["data"]["object"]
    amount = payment_data["amount"] / 100  # Convert cents to dollars
    currency = payment_data["currency"]
    customer_email = payment_data["billing_details"]["email"]
    
    # Your business logic here
    print(f"Payment of {amount} {currency} from {customer_email}")
    
    # Update your database
    # order_id = payment_data["metadata"]["order_id"]
    # update_order_status(order_id, "paid")
    
    # Return success (this gets sent back to Stripe)
    return {"status": "processed"}

# This function runs when a payment fails
@processor.on("payment.failed")
def handle_payment_failed(event):
    payment_data = event.payload["data"]["object"]
    error = payment_data["last_payment_error"]
    
    # Your business logic here
    print(f"Payment failed: {error['message']}")
    
    # Maybe notify the customer
    # customer_email = payment_data["billing_details"]["email"]
    # send_payment_failed_email(customer_email)
    
    return {"status": "handled"}

# Optional: Add code that runs for ALL events
@processor.use
def log_all_events(event):
    """This runs for every event before the specific handler"""
    print(f"Received {event.type} event at {event.timestamp}")
    # You could log events to a database here
```

## Step 4: Connect to Your Web Framework

The final step is connecting your webhook handlers to a web framework so they can receive HTTP requests.

### Option 1: Flask (Simple)

```python
# app.py
from flask import Flask
from smart_api_integrations.frameworks.flask import register_webhook_routes

# Import your handlers (this activates them)
import webhook_handlers

# Create a Flask app
app = Flask(__name__)

# Add webhook routes to your app (creates URLs like /webhooks/stripe/)
register_webhook_routes(app)

# Start the server
if __name__ == '__main__':
    print("Starting webhook server at http://localhost:5000")
    print("Available webhook URLs:")
    print("- http://localhost:5000/webhooks/stripe/")
    app.run(debug=True)
```

### Option 2: Django

```python
# urls.py
from django.urls import path
from smart_api_integrations.frameworks.django import webhook_view

# Import your handlers (this activates them)
import webhook_handlers

# Add to your urlpatterns
urlpatterns = [
    # Creates URLs like /webhooks/stripe/
    path('webhooks/<str:provider>/', webhook_view, name='webhook'),
    path('webhooks/<str:provider>/<str:webhook_name>/', webhook_view, name='webhook_named'),
    # ... your other URLs ...
]
```

### Option 3: FastAPI

```python
# main.py
from fastapi import FastAPI
from smart_api_integrations.frameworks.fastapi import register_webhook_routes

# Import your handlers (this activates them)
import webhook_handlers

# Create FastAPI app
app = FastAPI()

# Add webhook routes
register_webhook_routes(app)

# Start the server
if __name__ == '__main__':
    import uvicorn
    print("Starting webhook server at http://localhost:8000")
    print("Available webhook URLs:")
    print("- http://localhost:8000/webhooks/stripe/")
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Step 5: Register Your Webhook URL with the Service

After starting your web server, you'll need to tell the service (like Stripe) where to send webhooks.

### Getting a Public URL for Testing

For development, you'll need a way for external services to reach your local server. [Ngrok](https://ngrok.com/) is perfect for this:

```bash
# Install ngrok
npm install -g ngrok  # or download from ngrok.com

# Start your webhook server in one terminal
python app.py  # or python manage.py runserver for Django

# In another terminal, create a tunnel to your local server
ngrok http 5000  # use 8000 for Django/FastAPI
```

Ngrok will give you a public URL like `https://a1b2c3d4.ngrok.io` that forwards to your local server.

### Registering with the Service

Go to your service provider's dashboard and register your webhook URL:

#### For Stripe:
1. Go to [Stripe Dashboard](https://dashboard.stripe.com/) → Developers → Webhooks
2. Click "Add endpoint"
3. Enter your ngrok URL + the webhook path: `https://a1b2c3d4.ngrok.io/webhooks/stripe/`
4. Select the events you want to receive (like `payment_intent.succeeded`)
5. Save and copy the "Signing secret" to your environment variable

#### For GitHub:
1. Go to your GitHub repository → Settings → Webhooks
2. Click "Add webhook"
3. Enter your URL: `https://a1b2c3d4.ngrok.io/webhooks/github/`
4. Set content type to `application/json`
5. Enter your secret
6. Choose which events to receive
7. Save

### Testing Your Webhook

You can test your webhook without waiting for real events:

```bash
# Using our CLI tool
smart-api-integrations test-webhook stripe --event payment.succeeded --payload test_payment.json

# Or directly from the service dashboard (Stripe has a "Send test webhook" button)
```

## Advanced Webhook Features

Now that you have the basics working, here are some advanced features you can use:

### Advanced Configuration Options

Your webhook.yaml file supports these advanced features:

#### 1. IP Whitelisting (Security)
```yaml
# Only accept webhooks from these IPs
ip_whitelist:
  - 192.168.1.1
  - 10.0.0.0/24  # Entire subnet
```

#### 2. Rate Limiting (Prevent Abuse)
```yaml
webhooks:
  default:
    # ... other settings ...
    rate_limit:
      requests_per_minute: 60
      burst_limit: 10
```

#### 3. Multiple Webhooks for One Provider
```yaml
webhooks:
  default:
    path: /webhooks/github/
    # ... settings ...
  
  deployments:
    path: /webhooks/github/deployments/
    # Different settings for deployment events
```

#### 4. Custom Verification Logic
For providers with unique signature methods:

```python
from smart_api_integrations.core.webhook import WebhookVerifier

class MyCustomVerifier(WebhookVerifier):
    def verify(self, payload, signature, secret, **kwargs):
        # Your custom verification logic
        return True  # Replace with actual verification

# Use your custom verifier
registry = get_webhook_registry()
processor = registry.create_processor("my_provider")
processor.verifier = MyCustomVerifier()
```

### Built-in Provider Support

These providers have ready-to-use configurations:

- **Stripe**: Payment events (`payment.succeeded`, `payment.failed`, etc.)
- **GitHub**: Repository events (`push`, `pull_request`, etc.)
- **Slack**: Workspace events (`message`, `app_mention`, etc.)

For any other provider, just create your own webhook.yaml file.

### Troubleshooting Tips

If your webhooks aren't working:

1. **Check your logs** - Enable debug logging to see what's happening:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   logging.getLogger('smart_api_integrations.core.webhook').setLevel(logging.DEBUG)
   ```

2. **Verify your secret** - Make sure the environment variable has the correct secret

3. **Check the signature header** - Different services use different header names:
   - Stripe: `Stripe-Signature`
   - GitHub: `X-Hub-Signature-256`
   - Slack: `X-Slack-Signature`

4. **Test locally first** - Use the CLI tool to test without external services:
   ```bash
   smart-api-integrations test-webhook stripe --event payment.succeeded
   ```

### Security Best Practices

1. **Always verify signatures** in production
2. **Use environment variables** for secrets, never hardcode them
3. **Use HTTPS** for all webhook endpoints
4. **Add IP whitelisting** when possible
5. **Handle duplicate events** gracefully (events may be sent more than once)

### Quick Reference

| Provider | Environment Variable | Signature Header |
|----------|---------------------|------------------|
| Stripe | `STRIPE_WEBHOOK_SECRET` | `Stripe-Signature` |
| GitHub | `GITHUB_WEBHOOK_SECRET` | `X-Hub-Signature-256` |
| Slack | `SLACK_SIGNING_SECRET` | `X-Slack-Signature` | 