"""
Webhook integration helpers for existing applications.
"""

import os
import logging
from typing import Dict, List, Optional, Union, Callable, Type

logger = logging.getLogger(__name__)


def get_webhook_routes(
    framework: str,
    prefix: str = '/webhooks',
    providers: Optional[List[str]] = None
) -> object:
    """
    Get webhook routes for integration into an existing application.
    
    Args:
        framework: Web framework ('flask', 'fastapi', or 'django')
        prefix: URL prefix for webhook routes
        providers: Optional list of providers to enable
    
    Returns:
        Routes object appropriate for the framework
    
    Examples:
        # Flask - Blueprint
        from flask import Flask
        app = Flask(__name__)
        webhook_blueprint = get_webhook_routes('flask')
        app.register_blueprint(webhook_blueprint)
        
        # FastAPI - Router
        from fastapi import FastAPI
        app = FastAPI()
        webhook_router = get_webhook_routes('fastapi')
        app.include_router(webhook_router)
        
        # Django - URL patterns
        # In urls.py
        from django.urls import path, include
        urlpatterns = [
            path('api/', include(get_webhook_routes('django'))),
        ]
    """
    if framework.lower() == 'flask':
        return _get_flask_routes(prefix)
    elif framework.lower() == 'fastapi':
        return _get_fastapi_routes(prefix)
    elif framework.lower() == 'django':
        return _get_django_routes()
    else:
        raise ValueError(f"Unsupported framework: {framework}. Use 'flask', 'fastapi', or 'django'.")


def _get_flask_routes(prefix: str = '/webhooks'):
    """Get Flask blueprint for webhook routes."""
    try:
        from ..frameworks.flask import create_flask_blueprint
    except ImportError:
        raise ImportError("Flask is not installed. Install with: pip install flask")
    
    return create_flask_blueprint(url_prefix=prefix)


def _get_fastapi_routes(prefix: str = '/api'):
    """Get FastAPI router for webhook routes."""
    try:
        from ..frameworks.fastapi import create_fastapi_router
    except ImportError:
        raise ImportError("FastAPI is not installed. Install with: pip install fastapi")
    
    return create_fastapi_router()


def _get_django_routes():
    """Get Django URL patterns for webhook routes."""
    try:
        from ..frameworks.django import get_webhook_urls
    except ImportError:
        raise ImportError("Django is not installed. Install with: pip install django")
    
    return get_webhook_urls()


def generate_webhook_handler(
    provider: str,
    events: List[str] = None,
    class_name: Optional[str] = None
) -> Type:
    """
    Generate a provider-specific webhook handler class.
    
    Args:
        provider: Provider name (e.g., 'github', 'stripe')
        events: List of events to handle
        class_name: Optional class name (defaults to '{Provider}WebhookHandler')
    
    Returns:
        A WebhookHandler subclass for the provider
    
    Examples:
        # Generate a GitHub webhook handler class
        GitHubHandler = generate_webhook_handler(
            'github', 
            events=['push', 'pull_request']
        )
        
        # Instantiate the handler
        handler = GitHubHandler()
        
        # Or extend it with custom methods
        class MyGitHubHandler(GitHubHandler):
            def on_push(self, event):
                # Custom push handling
                return self.success_response({'processed': True})
    """
    from .handlers import WebhookHandler
    
    # Default class name if not provided
    if not class_name:
        class_name = f"{provider.title()}WebhookHandler"
    
    # Create the handler class
    handler_class = type(
        class_name,
        (WebhookHandler,),
        {
            'provider': provider,
            '__doc__': f"{provider.title()} webhook handler."
        }
    )
    
    # Add event handler methods if events are provided
    if events:
        for event in events:
            method_name = f"on_{event.replace('.', '_')}"
            
            # Define a handler method
            def event_handler(self, event, event_type=event):
                """Handle event."""
                logger.info(f"Received {provider} {event_type} event")
                return self.success_response({
                    'event_type': event_type,
                    'processed': True
                })
            
            # Add method to the class
            setattr(handler_class, method_name, event_handler)
    
    return handler_class 