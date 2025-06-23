"""
FastAPI integration for Smart API webhook system.
"""

import logging
import json
from typing import Optional, Dict, Any
from fastapi import FastAPI, Request, Response, HTTPException, Depends, APIRouter

from smart_api_integrations.core.webhook_registry import get_webhook_registry
from smart_api_integrations.core.webhook_schema import WebhookResponse

logger = logging.getLogger(__name__)


async def process_webhook(
    request: Request, provider: str, webhook_name: Optional[str] = None
):
    """Process a webhook request."""
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
            return {
                "success": False,
                "message": f"No webhook processor found for {provider}:{webhook_name}",
            }

        # Read the request body
        body = await request.body()

        # Create a Django-like request object for compatibility
        django_request = type(
            "HttpRequest",
            (),
            {
                "body": body,
                "META": {
                    f"HTTP_{k.upper().replace('-', '_')}": v
                    for k, v in request.headers.items()
                },
                "method": request.method,
                "path": request.url.path,
            },
        )

        # Verify signature
        if not processor.verify_signature(django_request):
            logger.warning(f"Signature verification failed for {processor_key}")
            return {"success": False, "message": "Signature verification failed"}

        # Parse event
        event = processor.parse_event(django_request)

        # Process event
        response = processor.process(event)

        # Return response
        return response.dict()

    except Exception as e:
        logger.error(f"Webhook processing error: {e}", exc_info=True)
        return {"success": False, "message": f"Error processing webhook: {str(e)}"}


def register_webhook_routes(app: FastAPI, prefix: str = "/webhooks"):
    """Register webhook routes with a FastAPI app."""
    router = APIRouter()

    @router.post("/{provider}/")
    async def handle_provider_webhook(request: Request, provider: str):
        """Handle webhook for a provider."""
        result = await process_webhook(request, provider)
        status_code = result.get("status_code", 200)
        return Response(
            content=json.dumps(result),
            media_type="application/json",
            status_code=status_code,
        )

    @router.post("/{provider}/{webhook_name}/")
    async def handle_named_webhook(request: Request, provider: str, webhook_name: str):
        """Handle webhook for a provider and webhook name."""
        result = await process_webhook(request, provider, webhook_name)
        status_code = result.get("status_code", 200)
        return Response(
            content=json.dumps(result),
            media_type="application/json",
            status_code=status_code,
        )

    # Register the router with the app
    app.include_router(router, prefix=prefix)

    logger.info(
        f"Registered webhook routes: {prefix}/{{provider}}/ and {prefix}/{{provider}}/{{webhook_name}}/"
    )

    return router
