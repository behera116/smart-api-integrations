#!/usr/bin/env python3
"""
Simple Webhook Server Example

This example demonstrates how to create a complete webhook server with minimal code.
"""

import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

# Import the webhook server creator
try:
    from smart_api_integrations.webhooks import run_webhook_server, smart_webhook_handler
except ImportError:
    # For local development
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from src.webhooks import run_webhook_server, smart_webhook_handler

# Define webhook handlers
@smart_webhook_handler('github', 'push')
def handle_github_push(event):
    """Handle GitHub push events."""
    repo = event.payload.get('repository', {}).get('name', 'unknown')
    commits = event.payload.get('commits', [])
    
    print(f"🔔 GitHub Push: {repo} - {len(commits)} commits")
    
    return {
        'success': True,
        'message': f"Processed push to {repo}"
    }

@smart_webhook_handler('stripe', 'payment_intent.succeeded')
def handle_payment_success(event):
    """Handle Stripe payment success events."""
    payment = event.payload.get('data', {}).get('object', {})
    amount = payment.get('amount', 0) / 100  # Convert cents to dollars
    
    print(f"💰 Payment Received: ${amount:.2f}")
    
    return {
        'success': True,
        'message': f"Processed payment of ${amount:.2f}"
    }

if __name__ == "__main__":
    # Set webhook secrets for testing (in production, set in environment)
    # os.environ['GITHUB_WEBHOOK_SECRET'] = 'your_github_webhook_secret'
    # os.environ['STRIPE_WEBHOOK_SECRET'] = 'your_stripe_webhook_secret'
    
    # Run the webhook server with both GitHub and Stripe providers
    print("🚀 Starting webhook server...")
    print("📌 Endpoints:")
    print("   - GitHub: http://localhost:5000/webhooks/github")
    print("   - Stripe: http://localhost:5000/webhooks/stripe")
    print("🛑 Press Ctrl+C to stop")
    
    # Create and run the server in one line!
    run_webhook_server(
        providers=['github', 'stripe'],
        port=5000,
        debug=True
    ) 