#!/usr/bin/env python3
"""
Example script demonstrating how to use the webhook system.

This example shows how to:
1. Create a webhook configuration
2. Register webhook handlers
3. Process webhook events
4. Integrate with a web framework (Flask)
"""

import os
import sys
import json
from pathlib import Path

# Add the parent directory to the path so we can import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import required modules
from src.smart_api_integrations.core.webhook_registry import get_webhook_registry
from src.smart_api_integrations.core.webhook_schema import (
    WebhookConfig,
    WebhookVerificationType,
)

# Try to import Flask (optional for the example)
try:
    from flask import Flask

    FLASK_AVAILABLE = True
except ImportError:
    print("Flask is not installed. Web server functionality will be disabled.")
    FLASK_AVAILABLE = False


def setup_webhook_config():
    """Set up a webhook configuration for the example."""
    # Create the providers directory if it doesn't exist
    providers_dir = (
        Path(__file__).parent.parent
        / "src"
        / "smart_api_integrations"
        / "providers"
        / "example"
    )
    providers_dir.mkdir(exist_ok=True, parents=True)

    # Create a webhook.yaml file
    webhook_yaml = """
# Provider-level configuration
default_verification_type: hmac_sha256
default_signature_header: X-Signature

# Webhook configurations
webhooks:
  default:
    path: /webhooks/example/
    verify_signature: true
    signing_secret_env: EXAMPLE_WEBHOOK_SECRET
    verification_type: hmac_sha256
    signature_header: X-Signature
    events:
      - order.created
      - order.updated
      - order.deleted
    """

    webhook_file = providers_dir / "webhook.yaml"
    with open(webhook_file, "w") as f:
        f.write(webhook_yaml)

    print(f"Created webhook configuration at {webhook_file}")

    # Set the environment variable for the webhook secret
    os.environ["EXAMPLE_WEBHOOK_SECRET"] = "example_secret"
    print("Set EXAMPLE_WEBHOOK_SECRET environment variable")


def register_webhook_handlers():
    """Register webhook handlers for the example."""
    # Get the webhook registry
    registry = get_webhook_registry()

    # Create a webhook processor
    processor = registry.create_processor("example", "default")

    # Define event handlers
    def handle_order_created(event):
        """Handle order created event."""
        order_id = event.payload.get("order_id", "unknown")
        print(f"Order created: {order_id}")
        print(f"Order details: {json.dumps(event.payload, indent=2)}")
        return {"status": "processed", "order_id": order_id}

    def handle_order_updated(event):
        """Handle order updated event."""
        order_id = event.payload.get("order_id", "unknown")
        print(f"Order updated: {order_id}")
        print(f"Updated fields: {event.payload.get('updated_fields', [])}")
        return {"status": "processed", "order_id": order_id}

    def handle_order_deleted(event):
        """Handle order deleted event."""
        order_id = event.payload.get("order_id", "unknown")
        print(f"Order deleted: {order_id}")
        return {"status": "processed", "order_id": order_id}

    # Define middleware
    def log_events(event):
        """Log all events."""
        print(f"Received event: {event.type} from {event.provider}")
        print(f"Event ID: {event.id}")
        print(f"Timestamp: {event.timestamp}")

    # Register event handlers
    processor.on("order.created", handle_order_created)
    processor.on("order.updated", handle_order_updated)
    processor.on("order.deleted", handle_order_deleted)

    # Add middleware
    processor.use(log_events)

    print("Registered webhook handlers")
    return processor


def create_flask_app():
    """Create a Flask app with webhook routes."""
    if not FLASK_AVAILABLE:
        print("Flask is not installed. Cannot create Flask app.")
        return None

    app = Flask(__name__)

    try:
        # Import the webhook view
        from src.smart_api_integrations.frameworks.flask import register_webhook_routes

        # Register webhook routes
        register_webhook_routes(app)

        # Add a simple home page
        @app.route("/")
        def home():
            return """
            <html>
                <head><title>Webhook Example</title></head>
                <body>
                    <h1>Webhook Example</h1>
                    <p>Available webhook endpoints:</p>
                    <ul>
                        <li><a href="/webhooks/example/">/webhooks/example/</a> - Default webhook endpoint</li>
                    </ul>
                    <p>Use a tool like <a href="https://ngrok.com/">ngrok</a> to expose this server to the internet.</p>
                    <p>Then register the webhook URL with the third-party service.</p>
                </body>
            </html>
            """

        return app
    except ImportError as e:
        print(f"Could not set up Flask routes: {e}")
        return None


def simulate_webhook_request(processor):
    """Simulate a webhook request."""
    from src.smart_api_integrations.core.webhook_schema import WebhookEvent
    from datetime import datetime, timezone
    import hmac
    import hashlib

    # Create a sample payload
    payload = {
        "event_id": "evt_123456",
        "type": "order.created",
        "order_id": "ord_123456",
        "customer_id": "cus_123456",
        "amount": 100.00,
        "currency": "USD",
        "status": "pending",
        "created_at": "2023-01-01T12:00:00Z",
    }

    # Convert payload to bytes
    payload_bytes = json.dumps(payload).encode("utf-8")

    # Create a signature
    secret = "example_secret"
    signature = hmac.new(
        secret.encode("utf-8"), payload_bytes, hashlib.sha256
    ).hexdigest()

    # Create a webhook event
    event = WebhookEvent(
        id="evt_123456",
        type="order.created",
        provider="example",
        webhook_name="default",
        payload=payload,
        headers={"X-Signature": f"sha256={signature}"},
        timestamp=datetime.now(timezone.utc),
        raw_body=payload_bytes,
    )

    # Process the event
    response = processor.process(event)

    print("\nSimulated Webhook Request:")
    print(f"Event: {event.type}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print(f"Response: {json.dumps(response.dict(), indent=2)}")


def main():
    """Main function to demonstrate the webhook system."""
    print("Setting up webhook configuration...")
    setup_webhook_config()

    print("\nRegistering webhook handlers...")
    processor = register_webhook_handlers()

    print("\nSimulating a webhook request...")
    simulate_webhook_request(processor)

    print("\nCreating Flask app with webhook routes...")
    app = create_flask_app()

    print("\nWebhook setup complete!")
    if FLASK_AVAILABLE and app:
        print("To start the Flask server, run:")
        print("  flask --app examples.webhook_handler_example:app run")
        print("\nThen use a tool like ngrok to expose your server to the internet:")
        print("  ngrok http 5000")

        # Uncomment to run the Flask app directly
        # app.run(debug=True)
    else:
        print(
            "\nTo use webhooks with a web framework, install Flask, Django, or FastAPI."
        )
        print("Then integrate with your application as shown in the documentation.")


if __name__ == "__main__":
    main()
