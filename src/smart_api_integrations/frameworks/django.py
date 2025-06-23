"""
Django integration for Smart API webhook system.
"""

import logging
import json
from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from typing import Optional

from smart_api_integrations.core.webhook_registry import get_webhook_registry
from smart_api_integrations.core.webhook_schema import WebhookResponse

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def webhook_view(
    request: HttpRequest, provider: str, webhook_name: Optional[str] = None
):
    """Django view function for handling webhook requests."""
    try:
        # Get the webhook registry
        registry = get_webhook_registry()

        # Use 'default' if webhook_name is not provided
        webhook_name = webhook_name or "default"

        # Get the webhook processor
        processor_key = f"{provider}:{webhook_name}"
        processor = registry.get_processor(processor_key)

        if not processor:
            logger.warning(f"No webhook processor found for {processor_key}")
            return JsonResponse(
                {
                    "success": False,
                    "message": f"No webhook processor found for {provider}:{webhook_name}",
                },
                status=404,
            )

        # Verify signature
        if not processor.verify_signature(request):
            logger.warning(f"Signature verification failed for {processor_key}")
            return JsonResponse(
                {"success": False, "message": "Signature verification failed"},
                status=401,
            )

        # Parse event
        event = processor.parse_event(request)

        # Process event
        response = processor.process(event)

        # Return response
        return JsonResponse(response.dict(), status=response.status_code)

    except Exception as e:
        logger.error(f"Webhook processing error: {e}", exc_info=True)
        return JsonResponse(
            {"success": False, "message": f"Error processing webhook: {str(e)}"},
            status=500,
        )


def register_webhook_urls():
    """Generate Django URL patterns for webhooks."""
    from django.urls import path

    urlpatterns = [
        path("webhooks/<str:provider>/", webhook_view, name="webhook"),
        path(
            "webhooks/<str:provider>/<str:webhook_name>/",
            webhook_view,
            name="webhook_named",
        ),
    ]

    logger.info("Registered webhook URL patterns")

    return urlpatterns


@csrf_exempt
def webhook_status_view(
    request: HttpRequest, provider: str, webhook_name: str = "default"
):
    """Django view for checking webhook status."""
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    return JsonResponse(
        {
            "provider": provider,
            "webhook_name": webhook_name,
            "status": "ready",
            "method": "POST",
        }
    )


def get_webhook_urls():
    """Get Django URL patterns for webhooks."""
    return [
        path("webhooks/<str:provider>/", webhook_view, name="webhook_default"),
        path(
            "webhooks/<str:provider>/<str:webhook_name>/",
            webhook_view,
            name="webhook_named",
        ),
        path(
            "webhooks/<str:provider>/status/",
            webhook_status_view,
            name="webhook_status_default",
        ),
        path(
            "webhooks/<str:provider>/<str:webhook_name>/status/",
            webhook_status_view,
            name="webhook_status_named",
        ),
    ]


def init_django_app(urlpatterns: List, prefix: str = ""):
    """Initialize Django app with Smart API webhooks."""
    # Add webhook URLs to the provided urlpatterns
    from django.urls import include, path

    if prefix:
        urlpatterns.append(path(f'{prefix.strip("/")}/', include(get_webhook_urls())))
    else:
        urlpatterns.extend(get_webhook_urls())

    logger.info("Smart API webhook URLs added to Django urlpatterns")


# Stub implementations when Django is not available
def get_webhook_urls():
    """Stub implementation when Django is not available."""
    raise ImportError(
        "Django is not installed. Install with: pip install smart-api-client[django]"
    )


def init_django_app(urlpatterns, prefix: str = ""):
    """Stub implementation when Django is not available."""
    raise ImportError(
        "Django is not installed. Install with: pip install smart-api-client[django]"
    )
