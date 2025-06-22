#!/usr/bin/env python3
"""
Webhook Integration Example

This example demonstrates how to integrate webhooks into an existing application.
"""

import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the webhook integration helpers
try:
    from smart_api_integrations.webhooks import smart_webhook_handler, generate_webhook_handler
    from smart_api_integrations.webhooks import get_webhook_routes
except ImportError:
    # For local development
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from src.webhooks import smart_webhook_handler, generate_webhook_handler
    from src.webhooks import get_webhook_routes

# Example 1: Function-based webhook handler
@smart_webhook_handler('github', 'push')
def handle_github_push(event):
    """Handle GitHub push events."""
    repo = event.payload.get('repository', {}).get('name', 'unknown')
    commits = event.payload.get('commits', [])
    
    logger.info(f"Received push to {repo} with {len(commits)} commits")
    
    return {
        'success': True,
        'message': f"Processed push to {repo}"
    }

# Example 2: Generate a provider-specific webhook handler class
StripeWebhookHandler = generate_webhook_handler(
    'stripe',
    events=['payment_intent.succeeded', 'payment_intent.payment_failed', 'customer.created'],
    class_name='StripePaymentHandler'
)

# Example 3: Extend the generated handler with custom methods
class CustomStripeHandler(StripeWebhookHandler):
    """Custom Stripe webhook handler with additional business logic."""
    
    def on_payment_intent_succeeded(self, event):
        """Handle successful payment with custom logic."""
        payment_intent = event.payload.get('data', {}).get('object', {})
        amount = payment_intent.get('amount', 0) / 100  # Convert cents to dollars
        
        logger.info(f"Payment received: ${amount:.2f}")
        
        # Add business logic here
        # - Update order status
        # - Send confirmation email
        # - Update inventory
        
        return self.success_response({
            'payment_id': payment_intent.get('id'),
            'amount': amount,
            'status': 'processed'
        })
    
    def on_customer_created(self, event):
        """Handle new customer creation."""
        customer = event.payload.get('data', {}).get('object', {})
        
        logger.info(f"New customer: {customer.get('email')}")
        
        return self.success_response({
            'customer_id': customer.get('id'),
            'email': customer.get('email')
        })

# Instantiate the handler
stripe_handler = CustomStripeHandler()

# Example 4: Integration with Flask
def create_flask_app():
    """Create a Flask app with webhook integration."""
    try:
        from flask import Flask, jsonify
    except ImportError:
        logger.error("Flask is not installed. Install with: pip install flask")
        return None
    
    # Create Flask app
    app = Flask(__name__)
    
    # Get webhook routes blueprint
    webhook_blueprint = get_webhook_routes('flask', prefix='/api/webhooks')
    
    # Register the blueprint
    app.register_blueprint(webhook_blueprint)
    
    # Add a regular route
    @app.route('/')
    def index():
        return jsonify({
            'message': 'Webhook Integration Example',
            'webhook_endpoints': {
                'github': '/api/webhooks/github',
                'stripe': '/api/webhooks/stripe'
            }
        })
    
    return app

# Example 5: Integration with FastAPI
def create_fastapi_app():
    """Create a FastAPI app with webhook integration."""
    try:
        from fastapi import FastAPI
    except ImportError:
        logger.error("FastAPI is not installed. Install with: pip install fastapi")
        return None
    
    # Create FastAPI app
    app = FastAPI(title="Webhook Integration Example")
    
    # Get webhook routes router
    webhook_router = get_webhook_routes('fastapi')
    
    # Include the router
    app.include_router(webhook_router)
    
    # Add a regular route
    @app.get('/')
    def index():
        return {
            'message': 'Webhook Integration Example',
            'webhook_endpoints': {
                'github': '/api/webhooks/github',
                'stripe': '/api/webhooks/stripe'
            }
        }
    
    return app

# Example 6: Integration with Django
def get_django_urlpatterns():
    """Get Django URL patterns with webhook integration."""
    try:
        from django.urls import path, include
    except ImportError:
        logger.error("Django is not installed. Install with: pip install django")
        return []
    
    # Get webhook URL patterns
    webhook_urls = get_webhook_routes('django')
    
    # Create URL patterns
    urlpatterns = [
        path('api/', include(webhook_urls)),
    ]
    
    return urlpatterns

if __name__ == "__main__":
    # Run the Flask app as an example
    app = create_flask_app()
    if app:
        print("\n🚀 Starting Flask app with webhook integration...")
        print("📌 Webhook endpoints:")
        print("   - GitHub: http://localhost:5000/api/webhooks/github")
        print("   - Stripe: http://localhost:5000/api/webhooks/stripe")
        print("🛑 Press Ctrl+C to stop")
        
        app.run(debug=True, port=5000)
    else:
        print("Install Flask to run this example: pip install flask") 