"""
Base classes for webhook handlers.
"""

from typing import Dict, Any
import logging

from ..core.webhook_schema import WebhookEvent, WebhookResponse
from ..core.webhook_registry import get_webhook_registry

logger = logging.getLogger(__name__)


class WebhookHandler:
    """
    Base class for webhook handlers.
    
    Example:
        class StripeWebhookHandler(WebhookHandler):
            provider = 'stripe'
            
            def on_payment_intent_succeeded(self, event):
                payment_intent = event.payload['data']['object']
                # Process payment
                return self.success_response({'payment_id': payment_intent['id']})
            
            def on_payment_intent_failed(self, event):
                payment_intent = event.payload['data']['object']
                # Handle failure
                return self.error_response('Payment failed', {'payment_id': payment_intent['id']})
    """
    
    provider: str = None
    webhook_name: str = 'default'
    
    def __init__(self):
        if not self.provider:
            raise ValueError("Provider name must be specified")
        self._register_handlers()
    
    def _register_handlers(self):
        """Register event handlers based on method names."""
        registry = get_webhook_registry()
        processor_key = f"{self.provider}:{self.webhook_name}"
        processor = registry.get_processor(processor_key)
        
        if not processor:
            try:
                processor = registry.create_processor(self.provider, self.webhook_name)
            except ValueError as e:
                logger.error(f"Failed to create processor: {e}")
                return
        
        # Find methods starting with on_
        for attr_name in dir(self):
            if attr_name.startswith('on_'):
                # Convert method name to event type
                # on_payment_intent_succeeded -> payment_intent.succeeded
                event_type = attr_name[3:].replace('_', '.')
                handler = getattr(self, attr_name)
                if callable(handler):
                    processor.on(event_type, handler)
                    logger.info(f"Registered handler {attr_name} for {event_type}")
    
    def success_response(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a success response."""
        return {
            'success': True,
            'data': data or {}
        }
    
    def error_response(self, message: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create an error response."""
        return {
            'success': False,
            'message': message,
            'data': data or {}
        }
    
    def webhook_response(self, success: bool, status_code: int = 200, 
                        message: str = None, data: Dict[str, Any] = None) -> WebhookResponse:
        """Create a WebhookResponse object."""
        return WebhookResponse(
            success=success,
            status_code=status_code,
            message=message,
            data=data
        )


class StripeWebhookHandler(WebhookHandler):
    """
    Example Stripe webhook handler with common event handlers.
    
    Usage:
        # Register the handler
        stripe_handler = StripeWebhookHandler()
        
        # Or extend it
        class MyStripeHandler(StripeWebhookHandler):
            def on_payment_intent_succeeded(self, event):
                # Custom logic
                result = super().on_payment_intent_succeeded(event)
                # Additional processing
                return result
    """
    
    provider = 'stripe'
    
    def on_payment_intent_succeeded(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle successful payment intent."""
        payment_intent = event.payload['data']['object']
        logger.info(f"Payment succeeded: {payment_intent['id']}")
        
        return self.success_response({
            'payment_id': payment_intent['id'],
            'amount': payment_intent['amount'],
            'currency': payment_intent['currency']
        })
    
    def on_payment_intent_failed(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle failed payment intent."""
        payment_intent = event.payload['data']['object']
        logger.warning(f"Payment failed: {payment_intent['id']}")
        
        return self.success_response({
            'payment_id': payment_intent['id'],
            'status': 'failed'
        })
    
    def on_customer_created(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle new customer creation."""
        customer = event.payload['data']['object']
        logger.info(f"New customer created: {customer['id']}")
        
        return self.success_response({
            'customer_id': customer['id'],
            'email': customer.get('email')
        })


class GitHubWebhookHandler(WebhookHandler):
    """
    Example GitHub webhook handler with common event handlers.
    
    Usage:
        github_handler = GitHubWebhookHandler()
    """
    
    provider = 'github'
    
    def on_push(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle repository push events."""
        repository = event.payload['repository']
        commits = event.payload['commits']
        
        logger.info(f"Push to {repository['name']}: {len(commits)} commits")
        
        return self.success_response({
            'repository': repository['name'],
            'commits_count': len(commits),
            'ref': event.payload['ref']
        })
    
    def on_pull_request(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle pull request events."""
        action = event.payload['action']
        pull_request = event.payload['pull_request']
        
        logger.info(f"Pull request {action}: #{pull_request['number']}")
        
        return self.success_response({
            'action': action,
            'pr_number': pull_request['number'],
            'title': pull_request['title']
        })
    
    def on_issues(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle issue events."""
        action = event.payload['action']
        issue = event.payload['issue']
        
        logger.info(f"Issue {action}: #{issue['number']}")
        
        return self.success_response({
            'action': action,
            'issue_number': issue['number'],
            'title': issue['title']
        })


class SlackWebhookHandler(WebhookHandler):
    """
    Example Slack webhook handler with common event handlers.
    
    Usage:
        slack_handler = SlackWebhookHandler()
    """
    
    provider = 'slack'
    
    def on_message(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle message events."""
        message_event = event.payload['event']
        
        logger.info(f"Message in {message_event.get('channel')}")
        
        return self.success_response({
            'channel': message_event.get('channel'),
            'user': message_event.get('user'),
            'text': message_event.get('text', '')[:100]  # Truncate for logging
        })
    
    def on_app_mention(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle app mention events."""
        message_event = event.payload['event']
        
        logger.info(f"App mentioned in {message_event.get('channel')}")
        
        return self.success_response({
            'channel': message_event.get('channel'),
            'user': message_event.get('user'),
            'mentioned': True
        })
    
    def on_reaction_added(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle reaction added events."""
        reaction_event = event.payload['event']
        
        logger.info(f"Reaction added: {reaction_event.get('reaction')}")
        
        return self.success_response({
            'reaction': reaction_event.get('reaction'),
            'user': reaction_event.get('user')
        }) 