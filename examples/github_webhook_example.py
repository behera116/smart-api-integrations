#!/usr/bin/env python3
"""
GitHub Webhook Example

This example demonstrates how to create webhook handlers for GitHub events.
"""

import os
import logging
from smart_api_integrations.webhooks import smart_webhook_handler
from smart_api_integrations.webhooks.handlers import WebhookHandler
from smart_api_integrations.core.webhook_schema import WebhookEvent

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Example 1: Function-based webhook handler
@smart_webhook_handler('github', 'push')
def handle_github_push(event: WebhookEvent):
    """Handle GitHub push events."""
    repository = event.payload.get('repository', {})
    commits = event.payload.get('commits', [])
    
    logger.info(f"Push to {repository.get('name')}: {len(commits)} commits")
    
    # Process the push event
    # - Update deployment status
    # - Trigger CI/CD pipeline
    # - Send notifications
    
    return {
        'success': True,
        'message': 'Push event processed successfully',
        'data': {
            'repository': repository.get('name'),
            'commits_count': len(commits),
            'ref': event.payload.get('ref')
        }
    }

# Example 2: Class-based webhook handler
class GitHubWebhookHandler(WebhookHandler):
    """GitHub webhook handler with multiple event handlers."""
    
    provider = 'github'
    
    def on_pull_request(self, event: WebhookEvent):
        """Handle pull request events."""
        action = event.payload.get('action')
        pr = event.payload.get('pull_request', {})
        
        logger.info(f"Pull request {action}: #{pr.get('number')} - {pr.get('title')}")
        
        return self.success_response({
            'action': action,
            'pr_number': pr.get('number'),
            'title': pr.get('title')
        })
    
    def on_issues(self, event: WebhookEvent):
        """Handle issue events."""
        action = event.payload.get('action')
        issue = event.payload.get('issue', {})
        
        logger.info(f"Issue {action}: #{issue.get('number')} - {issue.get('title')}")
        
        return self.success_response({
            'action': action,
            'issue_number': issue.get('number'),
            'title': issue.get('title')
        })

# Initialize the class-based handler
github_handler = GitHubWebhookHandler()

# Example 3: Testing the handlers
if __name__ == "__main__":
    import json
    from smart_api_integrations.core.webhook_schema import WebhookEvent
    from datetime import datetime, timezone
    
    # Create a sample push event
    push_event = WebhookEvent(
        id="test_push_event",
        type="push",
        provider="github",
        webhook_name="default",
        payload={
            "repository": {
                "name": "test-repo",
                "full_name": "user/test-repo"
            },
            "commits": [
                {"id": "abc123", "message": "Test commit"}
            ],
            "ref": "refs/heads/main"
        },
        headers={},
        timestamp=datetime.now(timezone.utc),
        verified=True
    )
    
    # Process the event with our handler
    result = handle_github_push(push_event)
    print("Function-based handler result:")
    print(json.dumps(result, indent=2))
    
    # Create a sample pull request event
    pr_event = WebhookEvent(
        id="test_pr_event",
        type="pull_request",
        provider="github",
        webhook_name="default",
        payload={
            "action": "opened",
            "pull_request": {
                "number": 42,
                "title": "Add new feature"
            }
        },
        headers={},
        timestamp=datetime.now(timezone.utc),
        verified=True
    )
    
    # Process with class-based handler
    result = github_handler.on_pull_request(pr_event)
    print("\nClass-based handler result:")
    print(json.dumps(result, indent=2))
    
    print("\nTo set up with Flask:")
    print("""
    from flask import Flask
    from smart_api_integrations.frameworks.flask import init_flask_app
    
    app = Flask(__name__)
    init_flask_app(app)
    
    if __name__ == "__main__":
        app.run(debug=True)
    """) 