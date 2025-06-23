"""
Flask integration for Smart API.
Provides functions to integrate Smart API with Flask applications.
"""

from typing import Dict, Any, Optional, Callable
from flask import Blueprint, Flask, request, jsonify, current_app

from ..core.registry import get_client
from ..webhooks import process_webhook
from ..core.webhook_registry import get_webhook_registry
from ..core.webhook_schema import WebhookResponse

import logging
import json

logger = logging.getLogger(__name__)


def create_flask_blueprint(url_prefix: str = "/webhooks") -> Blueprint:
    """
    Create a Flask blueprint for Smart API webhooks.

    Args:
        url_prefix: URL prefix for webhook routes

    Returns:
        Flask Blueprint with webhook routes

    Example:
        from flask import Flask
        from smart_api_integrations.frameworks.flask import create_flask_blueprint

        app = Flask(__name__)
        webhook_bp = create_flask_blueprint('/api/webhooks')
        app.register_blueprint(webhook_bp)
    """
    bp = Blueprint("smart_api_webhooks", __name__, url_prefix=url_prefix)

    @bp.route("/<provider>/<event>", methods=["POST"])
    def webhook_handler(provider: str, event: str):
        """Handle webhook requests."""
        payload = request.json or {}
        headers = dict(request.headers)

        result = process_webhook(
            provider=provider,
            event=event,
            payload=payload,
            headers=headers,
            query_params=request.args.to_dict(),
            remote_addr=request.remote_addr,
        )

        if not result.success:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": result.error,
                        "details": result.error_details,
                    }
                ),
                result.status_code,
            )

        return jsonify({"success": True, "data": result.data}), 200

    return bp


def init_flask_app(app: Flask, url_prefix: str = "/webhooks") -> None:
    """Initialize a Flask app with Smart API webhooks."""
    webhook_bp = create_flask_blueprint(url_prefix)
    app.register_blueprint(webhook_bp)

    # Add Smart API client to app context
    @app.before_request
    def setup_smart_api():
        """Set up Smart API clients in app context."""
        if not hasattr(current_app, "smart_api_clients"):
            current_app.smart_api_clients = {}


def get_client_from_app(app: Flask, provider_name: str, **auth_overrides) -> Any:
    """Get a Smart API client from Flask app context."""
    if not hasattr(app, "smart_api_clients"):
        app.smart_api_clients = {}

    # Create a cache key based on provider and auth overrides
    cache_key = provider_name
    if auth_overrides:
        # Sort keys for consistent cache key
        sorted_overrides = sorted(auth_overrides.items())
        cache_key = f"{provider_name}:{sorted_overrides}"

    # Return cached client if available
    if cache_key in app.smart_api_clients:
        return app.smart_api_clients[cache_key]

    # Create new client
    from ..clients.universal import UniversalAPIClient

    client = UniversalAPIClient(provider_name, **auth_overrides)

    # Cache client
    app.smart_api_clients[cache_key] = client

    return client


def webhook_view(provider: str, webhook_name: Optional[str] = None):
    """Flask view function for handling webhook requests."""
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
            return (
                jsonify(
                    {
                        "success": False,
                        "message": f"No webhook processor found for {provider}:{webhook_name}",
                    }
                ),
                404,
            )

        # Verify signature
        if not processor.verify_signature(request):
            logger.warning(f"Signature verification failed for {processor_key}")
            return (
                jsonify({"success": False, "message": "Signature verification failed"}),
                401,
            )

        # Parse event
        event = processor.parse_event(request)

        # Process event
        response = processor.process(event)

        # Return response
        return jsonify(response.dict()), response.status_code

    except Exception as e:
        logger.error(f"Webhook processing error: {e}", exc_info=True)
        return (
            jsonify(
                {"success": False, "message": f"Error processing webhook: {str(e)}"}
            ),
            500,
        )


def register_webhook_routes(app, url_prefix: str = "/webhooks"):
    """Register webhook routes with a Flask app."""
    # Create a blueprint
    webhook_bp = Blueprint("webhooks", __name__)

    # Register routes
    @webhook_bp.route("/<provider>/", methods=["POST"])
    def handle_provider_webhook(provider):
        return webhook_view(provider)

    @webhook_bp.route("/<provider>/<webhook_name>/", methods=["POST"])
    def handle_named_webhook(provider, webhook_name):
        return webhook_view(provider, webhook_name)

    # Register the blueprint with the app
    app.register_blueprint(webhook_bp, url_prefix=url_prefix)

    logger.info(
        f"Registered webhook routes: {url_prefix}/<provider>/ and {url_prefix}/<provider>/<webhook_name>/"
    )

    return webhook_bp
