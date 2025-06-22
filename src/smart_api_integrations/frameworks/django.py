"""
Django integration for Smart API webhooks.
"""

import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

try:
    from django.urls import path
    from django.http import JsonResponse, HttpRequest
    from django.views.decorators.csrf import csrf_exempt
    from django.views.decorators.http import require_POST
    DJANGO_AVAILABLE = True
except ImportError:
    DJANGO_AVAILABLE = False
    logger.warning("Django not installed. Django integration unavailable.")

if DJANGO_AVAILABLE:
    from ..webhooks.base import WebhookRequest, BaseWebhookHandler


    class DjangoWebhookRequest(WebhookRequest):
        """Django request adapter for webhooks."""
        
        def __init__(self, request: HttpRequest):
            self.request = request
        
        def get_body(self) -> bytes:
            return self.request.body
        
        def get_headers(self) -> Dict[str, str]:
            return dict(self.request.headers)
        
        def get_method(self) -> str:
            return self.request.method
        
        def get_path(self) -> str:
            return self.request.path


    @csrf_exempt
    @require_POST
    def webhook_view(request: HttpRequest, provider: str, webhook_name: str = 'default'):
        """Django view for handling webhooks."""
        handler = BaseWebhookHandler()
        webhook_request = DjangoWebhookRequest(request)
        
        response = handler.process_webhook(webhook_request, provider, webhook_name)
        
        return JsonResponse(
            response.data,
            status=response.status_code,
            headers=response.headers
        )


    @csrf_exempt
    def webhook_status_view(request: HttpRequest, provider: str, webhook_name: str = 'default'):
        """Django view for checking webhook status."""
        if request.method != 'GET':
            return JsonResponse({'error': 'Method not allowed'}, status=405)
        
        return JsonResponse({
            'provider': provider,
            'webhook_name': webhook_name,
            'status': 'ready',
            'method': 'POST'
        })


    def get_webhook_urls():
        """Get Django URL patterns for webhooks."""
        return [
            path('webhooks/<str:provider>/', webhook_view, name='webhook_default'),
            path('webhooks/<str:provider>/<str:webhook_name>/', webhook_view, name='webhook_named'),
            path('webhooks/<str:provider>/status/', webhook_status_view, name='webhook_status_default'),
            path('webhooks/<str:provider>/<str:webhook_name>/status/', webhook_status_view, name='webhook_status_named'),
        ]


    def init_django_app(urlpatterns: List, prefix: str = ''):
        """Initialize Django app with Smart API webhooks."""
        # Add webhook URLs to the provided urlpatterns
        from django.urls import include, path
        
        if prefix:
            urlpatterns.append(path(f'{prefix.strip("/")}/', include(get_webhook_urls())))
        else:
            urlpatterns.extend(get_webhook_urls())
        
        logger.info("Smart API webhook URLs added to Django urlpatterns")

else:
    # Stub implementations when Django is not available
    def get_webhook_urls():
        """Stub implementation when Django is not available."""
        raise ImportError("Django is not installed. Install with: pip install smart-api-client[django]")
    
    def init_django_app(urlpatterns, prefix: str = ''):
        """Stub implementation when Django is not available."""
        raise ImportError("Django is not installed. Install with: pip install smart-api-client[django]") 