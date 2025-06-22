"""
Smart API Webhook System.

Provides decorators and handlers for webhook processing.
"""

from .base import WebhookRequest, WebhookResponse, BaseWebhookHandler, SimpleWebhookRequest
from .handlers import webhook_middleware, WebhookHandler, process_webhook
from .decorators import smart_webhook_handler
from .server import get_webhook_routes, generate_webhook_handler

__all__ = [
    'WebhookRequest',
    'WebhookResponse',
    'BaseWebhookHandler',
    'SimpleWebhookRequest',
    'smart_webhook_handler',
    'webhook_middleware',
    'WebhookHandler',
    'process_webhook',
    'get_webhook_routes',
    'generate_webhook_handler',
] 