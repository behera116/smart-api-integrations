"""
Framework-agnostic webhook handling base.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
import json
import logging

from ..core.webhook_schema import WebhookEvent
from ..core.webhook_registry import get_webhook_registry

logger = logging.getLogger(__name__)


class WebhookRequest(ABC):
    """Abstract base for webhook requests across frameworks."""
    
    @abstractmethod
    def get_body(self) -> bytes:
        """Get request body as bytes."""
        pass
    
    @abstractmethod
    def get_headers(self) -> Dict[str, str]:
        """Get request headers."""
        pass
    
    @abstractmethod
    def get_method(self) -> str:
        """Get HTTP method."""
        pass
    
    @abstractmethod
    def get_path(self) -> str:
        """Get request path."""
        pass


class WebhookResponse:
    """Framework-agnostic webhook response."""
    
    def __init__(self, data: Dict[str, Any], status_code: int = 200, headers: Optional[Dict[str, str]] = None):
        self.data = data
        self.status_code = status_code
        self.headers = headers or {}


class BaseWebhookHandler:
    """Base webhook handler that's framework-agnostic."""
    
    def __init__(self):
        self.registry = get_webhook_registry()
    
    def process_webhook(self, request: WebhookRequest, provider: str, webhook_name: str = 'default') -> WebhookResponse:
        """Process webhook request and return response."""
        try:
            # Get processor
            processor_key = f"{provider}:{webhook_name}"
            processor = self.registry.get_processor(processor_key)
            
            if not processor:
                try:
                    processor = self.registry.create_processor(provider, webhook_name)
                except ValueError as e:
                    return WebhookResponse(
                        {'error': 'Unknown provider or webhook', 'details': str(e)},
                        status_code=404
                    )
            
            # Create a mock request object for signature verification
            mock_request = MockHttpRequest(
                body=request.get_body(),
                headers=request.get_headers(),
                method=request.get_method()
            )
            
            # Verify signature
            if not processor.verify_signature(mock_request):
                return WebhookResponse(
                    {'error': 'Invalid signature'},
                    status_code=401
                )
            
            # Parse event
            try:
                event = processor.parse_event(mock_request)
                event.verified = True
            except Exception as e:
                logger.error(f"Failed to parse webhook: {e}", exc_info=True)
                return WebhookResponse(
                    {'error': 'Invalid payload', 'details': str(e)},
                    status_code=400
                )
            
            # Process event
            response = processor.process(event)
            
            return WebhookResponse(
                response.dict(),
                status_code=response.status_code
            )
            
        except Exception as e:
            logger.error(f"Webhook processing error: {e}", exc_info=True)
            return WebhookResponse(
                {'error': 'Internal server error', 'details': str(e)},
                status_code=500
            )


class MockHttpRequest:
    """Mock HTTP request for framework-agnostic processing."""
    
    def __init__(self, body: bytes, headers: Dict[str, str], method: str):
        self.body = body
        self.META = self._convert_headers_to_meta(headers)
        self.method = method
    
    def _convert_headers_to_meta(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Convert headers to Django-style META format for compatibility."""
        meta = {}
        for key, value in headers.items():
            # Convert to uppercase and replace hyphens with underscores
            meta_key = f"HTTP_{key.upper().replace('-', '_')}"
            meta[meta_key] = value
        return meta


class SimpleWebhookRequest(WebhookRequest):
    """Simple implementation of WebhookRequest for standalone usage."""
    
    def __init__(self, body: bytes, headers: Dict[str, str], method: str = 'POST', path: str = '/webhook'):
        self._body = body
        self._headers = headers
        self._method = method
        self._path = path
    
    def get_body(self) -> bytes:
        return self._body
    
    def get_headers(self) -> Dict[str, str]:
        return self._headers
    
    def get_method(self) -> str:
        return self._method
    
    def get_path(self) -> str:
        return self._path
