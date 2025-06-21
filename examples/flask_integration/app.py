"""
Flask integration example for Smart API.
"""

import os
from flask import Flask, jsonify, request

from smart_api_integrations import SmartAPIClient
from smart_api_integrations.frameworks.flask import create_flask_blueprint, init_flask_app
from smart_api_integrations.webhooks import webhook_handler

# Create Flask app
app = Flask(__name__)

# Initialize Smart API with Flask
init_flask_app(app, url_prefix='/api')

# API endpoints
@app.route('/github/user')
def github_user():
    """Get GitHub user information."""
    github = SmartAPIClient('github')
    user = github.get_user()
    
    return jsonify({
        'user': user.data,
        'status': user.status_code
    })


@app.route('/github/repos')
def github_repos():
    """List GitHub repositories."""
    github = SmartAPIClient('github')
    
    per_page = request.args.get('per_page', 10, type=int)
    page = request.args.get('page', 1, type=int)
    
    repos = github.list_repos(params={
        'per_page': per_page,
        'page': page
    })
    
    return jsonify({
        'repos': repos.data,
        'count': len(repos.data),
        'page': page
    })


# Webhook handlers
@webhook_handler('stripe', 'payment_intent.succeeded')
def handle_payment(event):
    """Handle Stripe payment success."""
    payment = event.payload['data']['object']
    amount = payment['amount'] / 100
    
    app.logger.info(f"Payment received: ${amount} {payment['currency']}")
    
    return {
        'processed': True,
        'payment_id': payment['id'],
        'amount': amount
    }


@webhook_handler('github', 'push')
def handle_github_push(event):
    """Handle GitHub push events."""
    ref = event.payload.get('ref', '')
    commits = event.payload.get('commits', [])
    
    app.logger.info(f"Push to {ref} with {len(commits)} commits")
    
    return {
        'processed': True,
        'ref': ref,
        'commit_count': len(commits)
    }


if __name__ == '__main__':
    # Set up environment
    os.environ['GITHUB_TOKEN'] = 'your-token-here'
    os.environ['STRIPE_WEBHOOK_SECRET'] = 'your-webhook-secret'
    
    # Run the app
    app.run(debug=True, port=5000)
