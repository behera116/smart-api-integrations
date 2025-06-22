#!/usr/bin/env python3
"""
Flask Webhook Integration Example

This example demonstrates how to integrate Smart API webhooks with a Flask application.
"""

import os
from flask import Flask, jsonify

# Import Smart API webhook integration
try:
    from smart_api_integrations.frameworks.flask import init_flask_app
    from smart_api_integrations.webhooks import smart_webhook_handler
    from smart_api_integrations.core.webhook_schema import WebhookEvent
except ImportError:
    # For local development
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from src.frameworks.flask import init_flask_app
    from src.webhooks.decorators import smart_webhook_handler
    from src.core.webhook_schema import WebhookEvent

# Create Flask app
app = Flask(__name__)

# Initialize Smart API webhooks
init_flask_app(app)

# Define webhook handlers
@smart_webhook_handler('github', 'push')
def handle_github_push(event: WebhookEvent):
    """Handle GitHub push events."""
    repository = event.payload.get('repository', {})
    commits = event.payload.get('commits', [])
    
    app.logger.info(f"Push to {repository.get('name')}: {len(commits)} commits")
    
    return {
        'success': True,
        'message': 'Push event processed',
        'data': {
            'repository': repository.get('name'),
            'commits_count': len(commits)
        }
    }

@smart_webhook_handler('stripe', 'payment_intent.succeeded')
def handle_payment_success(event: WebhookEvent):
    """Handle Stripe payment success events."""
    payment_intent = event.payload.get('data', {}).get('object', {})
    
    app.logger.info(f"Payment succeeded: {payment_intent.get('id')}")
    
    return {
        'success': True,
        'message': 'Payment processed',
        'data': {
            'payment_id': payment_intent.get('id'),
            'amount': payment_intent.get('amount')
        }
    }

# Add a regular Flask route
@app.route('/')
def index():
    """Show webhook information."""
    webhook_urls = {
        'github': '/webhooks/github',
        'stripe': '/webhooks/stripe'
    }
    
    return jsonify({
        'message': 'Smart API Webhook Server',
        'webhook_urls': webhook_urls,
        'setup_instructions': {
            'github': 'Set GITHUB_WEBHOOK_SECRET environment variable',
            'stripe': 'Set STRIPE_WEBHOOK_SECRET environment variable'
        }
    })

if __name__ == '__main__':
    # Set webhook secrets for testing
    # In production, these should be set in the environment
    # os.environ['GITHUB_WEBHOOK_SECRET'] = 'your_github_webhook_secret'
    # os.environ['STRIPE_WEBHOOK_SECRET'] = 'your_stripe_webhook_secret'
    
    # Run the app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
    
    print(f"Webhook server running at http://localhost:{port}/")
    print("Available webhook URLs:")
    print("  - GitHub: http://localhost:{port}/webhooks/github")
    print("  - Stripe: http://localhost:{port}/webhooks/stripe") 