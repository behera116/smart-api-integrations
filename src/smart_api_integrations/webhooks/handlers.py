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


# Import the renamed decorator for backward compatibility
from .decorators import smart_webhook_handler as webhook_handler

# Deprecated - use smart_webhook_handler instead
def webhook_handler_deprecated(provider: str, event_type: str):
    """
    DEPRECATED: Use smart_webhook_handler instead.
    Decorator to register a webhook handler function.
    
    Example:
        @smart_webhook_handler('stripe', 'payment_intent.succeeded')
        def handle_payment(event):
            payment_intent = event.payload['data']['object']
            # Process payment
            return {'success': True}
    """
    import warnings
    warnings.warn(
        "webhook_handler is deprecated. Use smart_webhook_handler instead.",
        DeprecationWarning, 
        stacklevel=2
    )
    return webhook_handler(provider, event_type)


def webhook_middleware(provider: str = None):
    """
    Decorator to register a webhook middleware function.
    
    Example:
        @webhook_middleware('stripe')
        def log_webhook(event, next_handler):
            logger.info(f"Received {event.provider} webhook: {event.event_type}")
            return next_handler(event)
    """
    def decorator(func):
        registry = get_webhook_registry()
        
        if provider:
            # Register for specific provider
            processor_key = f"{provider}:default"
            processor = registry.get_processor(processor_key)
            
            if not processor:
                try:
                    processor = registry.create_processor(provider, 'default')
                except ValueError as e:
                    logger.error(f"Failed to create processor: {e}")
                    return func
            
            processor.use(func)
        else:
            # Register as global middleware
            registry.add_global_middleware(func)
        
        # Add attributes to the function for introspection
        func.__webhook_middleware__ = True
        func.__webhook_provider__ = provider
        
        logger.info(f"Registered webhook middleware for {provider or 'all providers'}")
        return func
    return decorator


def process_webhook(
    provider: str,
    event: str,
    payload: Dict[str, Any],
    headers: Dict[str, str] = None,
    query_params: Dict[str, str] = None,
    remote_addr: str = None
) -> WebhookResponse:
    """
    Process a webhook request.
    
    Args:
        provider: Provider name (e.g., 'stripe', 'github')
        event: Event type (e.g., 'payment_intent.succeeded', 'push')
        payload: Webhook payload (usually JSON body)
        headers: Request headers
        query_params: Query parameters
        remote_addr: Remote IP address
        
    Returns:
        WebhookResponse object with processing result
    """
    registry = get_webhook_registry()
    processor_key = f"{provider}:default"
    processor = registry.get_processor(processor_key)
    
    if not processor:
        try:
            processor = registry.create_processor(provider, 'default')
        except ValueError as e:
            logger.error(f"Failed to create processor: {e}")
            return WebhookResponse(
                success=False,
                status_code=400,
                message=f"Invalid provider: {provider}",
                error_details={"error": str(e)}
            )
    
    # Create webhook event
    webhook_event = WebhookEvent(
        provider=provider,
        event_type=event,
        payload=payload,
        headers=headers or {},
        query_params=query_params or {},
        remote_addr=remote_addr
    )
    
    # Process the webhook
    try:
        result = processor.process(webhook_event)
        
        if isinstance(result, WebhookResponse):
            return result
        
        if isinstance(result, dict) and "success" in result:
            return WebhookResponse(
                success=result.get("success", True),
                status_code=200 if result.get("success", True) else 400,
                message=result.get("message"),
                data=result.get("data")
            )
        
        # Default success response
        return WebhookResponse(
            success=True,
            status_code=200,
            data=result
        )
        
    except Exception as e:
        logger.exception(f"Error processing webhook {provider}:{event}")
        return WebhookResponse(
            success=False,
            status_code=500,
            message=f"Error processing webhook: {str(e)}",
            error_details={"exception": str(e)}
        ) 