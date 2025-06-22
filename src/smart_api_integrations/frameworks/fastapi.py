"""
FastAPI framework adapter for Smart API.
"""

import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

try:
    from fastapi import APIRouter, Request, Response, HTTPException
    from fastapi.responses import JSONResponse
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    logger.warning("FastAPI not installed. FastAPI integration unavailable.")

if FASTAPI_AVAILABLE:
    from ..webhooks.base import WebhookRequest, BaseWebhookHandler


    class FastAPIWebhookRequest(WebhookRequest):
        """FastAPI request adapter."""
        
        def __init__(self, request: Request, body: bytes):
            self.request = request
            self._body = body
        
        def get_body(self) -> bytes:
            return self._body
        
        def get_headers(self) -> dict:
            return dict(self.request.headers)
        
        def get_method(self) -> str:
            return self.request.method
        
        def get_path(self) -> str:
            return str(self.request.url.path)


    def create_fastapi_router() -> APIRouter:
        """
        Create FastAPI router for webhook handling.
        
        Returns:
            FastAPI router with webhook endpoints
            
        Example:
            from fastapi import FastAPI
            from smart_api_integrations.frameworks.fastapi import create_fastapi_router
            
            app = FastAPI()
            webhook_router = create_fastapi_router()
            app.include_router(webhook_router)
        """
        router = APIRouter()
        handler = BaseWebhookHandler()
        
        @router.post("/webhooks/{provider}/")
        @router.post("/webhooks/{provider}/{webhook_name}/")
        async def handle_webhook(
            request: Request,
            provider: str,
            webhook_name: str = 'default'
        ):
            # Read body once and store it
            body = await request.body()
            
            webhook_request = FastAPIWebhookRequest(request, body)
            response = handler.process_webhook(webhook_request, provider, webhook_name)
            
            return JSONResponse(
                content=response.data,
                status_code=response.status_code,
                headers=response.headers
            )
        
        @router.get("/webhooks/{provider}/")
        @router.get("/webhooks/{provider}/{webhook_name}/")
        async def webhook_status(
            provider: str,
            webhook_name: str = 'default'
        ):
            return {
                'provider': provider,
                'webhook_name': webhook_name,
                'status': 'ready',
                'method': 'POST'
            }
        
        return router


    def init_fastapi_app(app, prefix: str = "/api"):
        """Initialize FastAPI app with Smart API."""
        # Include webhook router
        webhook_router = create_fastapi_router()
        app.include_router(webhook_router, prefix=prefix)
        
        # Add startup event
        @app.on_event("startup")
        async def startup_event():
            logger.info("Smart API initialized for FastAPI")
        
        # Add custom exception handler
        @app.exception_handler(HTTPException)
        async def smart_api_exception_handler(request: Request, exc: HTTPException):
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "error": exc.detail,
                    "status_code": exc.status_code
                }
            )


    def create_fastapi_cli():
        """Create FastAPI CLI commands using Typer."""
        try:
            import typer
            
            cli = typer.Typer()
            
            @cli.command()
            def add_provider(
                name: str = typer.Option(..., help="Provider name"),
                base_url: str = typer.Option(..., help="Base URL"),
                auth: str = typer.Option("none", help="Authentication type")
            ):
                """Add a new API provider."""
                from ..cli import add_provider_command
                add_provider_command(name, base_url, auth)
            
            @cli.command()
            def test_webhook(
                provider: str = typer.Option(..., help="Provider name"),
                webhook: str = typer.Option(..., help="Webhook name")
            ):
                """Test webhook handler."""
                from ..cli import test_webhook_command
                test_webhook_command(provider, webhook)
            
            return cli
            
        except ImportError:
            logger.info("Typer not available, CLI commands not created")
            return None

else:
    # Provide stub implementations when FastAPI is not available
    def create_fastapi_router():
        raise ImportError("FastAPI is not installed. Install with: pip install smart-api-client[fastapi]")
    
    def init_fastapi_app(app, prefix: str = "/api"):
        raise ImportError("FastAPI is not installed. Install with: pip install smart-api-client[fastapi]")
    
    def create_fastapi_cli():
        raise ImportError("FastAPI is not installed. Install with: pip install smart-api-client[fastapi]")
