"""
Decorators for webhook handlers.
"""

import logging
from typing import Callable, Any, Dict
from functools import wraps

from ..core.webhook_registry import get_webhook_registry
from ..core.webhook_schema import WebhookEvent

logger = logging.getLogger(__name__)


def smart_webhook_handler(provider: str, event_type: str, webhook_name: str = 'default'):
    """
    Decorator for registering webhook event handlers.
    
    Args:
        provider: The webhook provider name (e.g., 'stripe', 'github')
        event_type: The event type to handle (e.g., 'payment_intent.succeeded')
        webhook_name: The webhook name (defaults to 'default')
    
    Example:
        @webhook_handler('stripe', 'payment_intent.succeeded')
        def handle_payment_success(event):
            payment_intent = event.payload['data']['object']
            # Process payment
            return {'processed': True, 'payment_id': payment_intent['id']}
        
        @webhook_handler('github', 'push', 'repo_updates')
        def handle_repo_push(event):
            repo = event.payload['repository']['name']
            commits = len(event.payload['commits'])
            return {'repo': repo, 'commits': commits}
    """
    def decorator(func: Callable[[WebhookEvent], Any]) -> Callable:
        @wraps(func)
        def wrapper(event: WebhookEvent) -> Any:
            try:
                return func(event)
            except Exception as e:
                logger.error(f"Webhook handler error in {func.__name__}: {e}", exc_info=True)
                raise
        
        # Register the handler
        try:
            registry = get_webhook_registry()
            processor = registry.get_processor(f"{provider}:{webhook_name}")
            
            if not processor:
                try:
                    processor = registry.create_processor(provider, webhook_name)
                except ValueError as e:
                    logger.error(f"Failed to create processor for {provider}:{webhook_name}: {e}")
                    return wrapper
            
            processor.on(event_type, wrapper)
            logger.info(f"Registered webhook handler {func.__name__} for {provider}:{event_type}")
            
        except Exception as e:
            logger.error(f"Failed to register webhook handler {func.__name__}: {e}")
        
        return wrapper
    
    return decorator


def webhook_middleware(provider: str, webhook_name: str = 'default'):
    """
    Decorator for registering webhook middleware.
    
    Middleware functions are called before event handlers and can:
    - Modify the event
    - Return a WebhookResponse to short-circuit processing
    - Perform logging, authentication, etc.
    
    Args:
        provider: The webhook provider name
        webhook_name: The webhook name (defaults to 'default')
    
    Example:
        @webhook_middleware('stripe')
        def log_webhook_events(event):
            logger.info(f"Received {event.type} from {event.provider}")
            # Return None to continue processing
            return None
        
        @webhook_middleware('github')
        def authenticate_github_webhook(event):
            # Check if event is from authorized source
            if not is_authorized(event.headers):
                return WebhookResponse(success=False, status_code=401, message="Unauthorized")
            return None
    """
    def decorator(func: Callable[[WebhookEvent], Any]) -> Callable:
        @wraps(func)
        def wrapper(event: WebhookEvent) -> Any:
            try:
                return func(event)
            except Exception as e:
                logger.error(f"Webhook middleware error in {func.__name__}: {e}", exc_info=True)
                raise
        
        # Register the middleware
        try:
            registry = get_webhook_registry()
            processor = registry.get_processor(f"{provider}:{webhook_name}")
            
            if not processor:
                try:
                    processor = registry.create_processor(provider, webhook_name)
                except ValueError as e:
                    logger.error(f"Failed to create processor for {provider}:{webhook_name}: {e}")
                    return wrapper
            
            processor.use(wrapper)
            logger.info(f"Registered webhook middleware {func.__name__} for {provider}")
            
        except Exception as e:
            logger.error(f"Failed to register webhook middleware {func.__name__}: {e}")
        
        return wrapper
    
    return decorator


def batch_webhook_handler(provider: str, event_types: list, webhook_name: str = 'default'):
    """
    Decorator for registering a single handler for multiple event types.
    
    Args:
        provider: The webhook provider name
        event_types: List of event types to handle
        webhook_name: The webhook name (defaults to 'default')
    
    Example:
        @batch_webhook_handler('stripe', [
            'payment_intent.succeeded',
            'payment_intent.failed',
            'payment_intent.canceled'
        ])
        def handle_payment_events(event):
            if event.type == 'payment_intent.succeeded':
                return handle_success(event)
            elif event.type == 'payment_intent.failed':
                return handle_failure(event)
            else:
                return handle_canceled(event)
    """
    def decorator(func: Callable[[WebhookEvent], Any]) -> Callable:
        @wraps(func)
        def wrapper(event: WebhookEvent) -> Any:
            try:
                return func(event)
            except Exception as e:
                logger.error(f"Batch webhook handler error in {func.__name__}: {e}", exc_info=True)
                raise
        
        # Register the handler for all event types
        try:
            registry = get_webhook_registry()
            processor = registry.get_processor(f"{provider}:{webhook_name}")
            
            if not processor:
                try:
                    processor = registry.create_processor(provider, webhook_name)
                except ValueError as e:
                    logger.error(f"Failed to create processor for {provider}:{webhook_name}: {e}")
                    return wrapper
            
            for event_type in event_types:
                processor.on(event_type, wrapper)
                logger.info(f"Registered batch handler {func.__name__} for {provider}:{event_type}")
            
        except Exception as e:
            logger.error(f"Failed to register batch webhook handler {func.__name__}: {e}")
        
        return wrapper
    
    return decorator 