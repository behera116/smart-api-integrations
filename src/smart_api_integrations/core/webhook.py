"""
Webhook processing core for Smart API webhook system.
"""

import hmac
import hashlib
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timezone
from django.http import HttpRequest

from .webhook_schema import (
    WebhookEvent, 
    WebhookResponse, 
    WebhookConfig, 
    WebhookVerificationType
)

logger = logging.getLogger(__name__)


class WebhookVerifier(ABC):
    """Abstract base class for webhook signature verification."""
    
    @abstractmethod
    def verify(self, payload: bytes, signature: str, secret: str, **kwargs) -> bool:
        """Verify webhook signature."""
        pass


class HMACWebhookVerifier(WebhookVerifier):
    """HMAC-based webhook signature verification."""
    
    def __init__(self, algorithm: str = 'sha256'):
        self.algorithm = algorithm
    
    def verify(self, payload: bytes, signature: str, secret: str, **kwargs) -> bool:
        """Verify HMAC signature."""
        try:
            if self.algorithm == 'sha256':
                expected = hmac.new(
                    secret.encode('utf-8'),
                    payload,
                    hashlib.sha256
                ).hexdigest()
            elif self.algorithm == 'sha1':
                expected = hmac.new(
                    secret.encode('utf-8'),
                    payload,
                    hashlib.sha1
                ).hexdigest()
            else:
                raise ValueError(f"Unsupported algorithm: {self.algorithm}")
            
            # Handle different signature formats
            if signature.startswith('sha256='):
                signature = signature[7:]
            elif signature.startswith('sha1='):
                signature = signature[5:]
            
            return hmac.compare_digest(expected, signature)
        except Exception as e:
            logger.error(f"HMAC verification failed: {e}")
            return False


class StripeWebhookVerifier(WebhookVerifier):
    """Stripe-specific webhook verification."""
    
    def verify(self, payload: bytes, signature: str, secret: str, **kwargs) -> bool:
        """Verify Stripe webhook signature."""
        try:
            # Parse Stripe signature header
            sig_parts = {}
            for part in signature.split(','):
                key, value = part.split('=', 1)
                sig_parts[key] = value
            
            timestamp = sig_parts.get('t')
            v1_signature = sig_parts.get('v1')
            
            if not timestamp or not v1_signature:
                return False
            
            # Check timestamp tolerance (5 minutes)
            current_time = datetime.now(timezone.utc).timestamp()
            if abs(current_time - int(timestamp)) > 300:
                return False
            
            # Verify signature
            signed_payload = f"{timestamp}.{payload.decode('utf-8')}"
            expected = hmac.new(
                secret.encode('utf-8'),
                signed_payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected, v1_signature)
        except Exception as e:
            logger.error(f"Stripe verification failed: {e}")
            return False


class GitHubWebhookVerifier(WebhookVerifier):
    """GitHub-specific webhook verification."""
    
    def verify(self, payload: bytes, signature: str, secret: str, **kwargs) -> bool:
        """Verify GitHub webhook signature."""
        try:
            if not signature.startswith('sha256='):
                return False
            
            signature = signature[7:]  # Remove 'sha256=' prefix
            expected = hmac.new(
                secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected, signature)
        except Exception as e:
            logger.error(f"GitHub verification failed: {e}")
            return False


class SlackWebhookVerifier(WebhookVerifier):
    """Slack-specific webhook verification."""
    
    def verify(self, payload: bytes, signature: str, secret: str, **kwargs) -> bool:
        """Verify Slack webhook signature."""
        try:
            timestamp = kwargs.get('timestamp')
            if not timestamp:
                return False
            
            # Check timestamp tolerance (5 minutes)
            current_time = datetime.now(timezone.utc).timestamp()
            if abs(current_time - int(timestamp)) > 300:
                return False
            
            # Create signature base string
            sig_basestring = f"v0:{timestamp}:{payload.decode('utf-8')}"
            expected = 'v0=' + hmac.new(
                secret.encode('utf-8'),
                sig_basestring.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected, signature)
        except Exception as e:
            logger.error(f"Slack verification failed: {e}")
            return False


class WebhookProcessor:
    """Main webhook processor that handles events and middleware."""
    
    def __init__(self, provider: str, webhook_name: str, config: WebhookConfig):
        self.provider = provider
        self.webhook_name = webhook_name
        self.config = config
        self.handlers: Dict[str, List[Callable]] = {}
        self.middleware: List[Callable] = []
        self.verifier = self._get_verifier()
    
    def _get_verifier(self) -> Optional[WebhookVerifier]:
        """Get appropriate verifier based on provider and config."""
        if not self.config.verify_signature:
            return None
        
        if self.provider == 'stripe':
            return StripeWebhookVerifier()
        elif self.provider == 'github':
            return GitHubWebhookVerifier()
        elif self.provider == 'slack':
            return SlackWebhookVerifier()
        elif self.config.verification_type == WebhookVerificationType.HMAC_SHA256:
            return HMACWebhookVerifier('sha256')
        elif self.config.verification_type == WebhookVerificationType.HMAC_SHA1:
            return HMACWebhookVerifier('sha1')
        else:
            return None
    
    def on(self, event_type: str, handler: Callable):
        """Register an event handler."""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
        logger.info(f"Registered handler for {event_type} in {self.provider}:{self.webhook_name}")
    
    def use(self, middleware: Callable):
        """Add middleware."""
        self.middleware.append(middleware)
    
    def verify_signature(self, request: HttpRequest) -> bool:
        """Verify webhook signature."""
        if not self.verifier:
            return True  # No verification required
        
        try:
            import os
            secret = os.getenv(self.config.signing_secret_env)
            if not secret:
                logger.error(f"Missing signing secret: {self.config.signing_secret_env}")
                return False
            
            signature = request.META.get(f'HTTP_{self.config.signature_header.upper().replace("-", "_")}')
            if not signature:
                logger.error(f"Missing signature header: {self.config.signature_header}")
                return False
            
            # Get timestamp if required
            timestamp = None
            if self.config.timestamp_header:
                timestamp = request.META.get(f'HTTP_{self.config.timestamp_header.upper().replace("-", "_")}')
            
            return self.verifier.verify(
                request.body,
                signature,
                secret,
                timestamp=timestamp
            )
        except Exception as e:
            logger.error(f"Signature verification failed: {e}")
            return False
    
    def parse_event(self, request: HttpRequest) -> WebhookEvent:
        """Parse incoming webhook request into WebhookEvent."""
        try:
            payload = json.loads(request.body.decode('utf-8'))
            
            # Extract event ID and type based on provider
            event_id = self._extract_event_id(payload)
            event_type = self._extract_event_type(payload)
            
            return WebhookEvent(
                id=event_id,
                type=event_type,
                provider=self.provider,
                webhook_name=self.webhook_name,
                payload=payload,
                headers=dict(request.META),
                timestamp=datetime.now(timezone.utc),
                raw_body=request.body
            )
        except Exception as e:
            logger.error(f"Failed to parse webhook event: {e}")
            raise
    
    def _extract_event_id(self, payload: Dict[str, Any]) -> str:
        """Extract event ID from payload based on provider."""
        if self.provider == 'stripe':
            return payload.get('id', 'unknown')
        elif self.provider == 'github':
            return payload.get('delivery', 'unknown')
        elif self.provider == 'slack':
            return payload.get('event_id', 'unknown')
        else:
            return payload.get('id', payload.get('event_id', 'unknown'))
    
    def _extract_event_type(self, payload: Dict[str, Any]) -> str:
        """Extract event type from payload based on provider."""
        if self.provider == 'stripe':
            return payload.get('type', 'unknown')
        elif self.provider == 'github':
            return payload.get('action', 'unknown')
        elif self.provider == 'slack':
            return payload.get('event', {}).get('type', 'unknown')
        else:
            return payload.get('type', payload.get('event_type', 'unknown'))
    
    def process(self, event: WebhookEvent) -> WebhookResponse:
        """Process webhook event through middleware and handlers."""
        try:
            # Run middleware
            for middleware in self.middleware:
                result = middleware(event)
                if isinstance(result, WebhookResponse):
                    return result
            
            # Find and run handlers
            handlers = self.handlers.get(event.type, [])
            if not handlers:
                logger.warning(f"No handlers for event type: {event.type}")
                return WebhookResponse(
                    success=True,
                    message=f"No handlers for event type: {event.type}"
                )
            
            results = []
            for handler in handlers:
                try:
                    result = handler(event)
                    if isinstance(result, dict):
                        results.append(result)
                    elif isinstance(result, WebhookResponse):
                        return result
                except Exception as e:
                    logger.error(f"Handler error: {e}", exc_info=True)
                    return WebhookResponse(
                        success=False,
                        status_code=500,
                        message=f"Handler error: {str(e)}"
                    )
            
            return WebhookResponse(
                success=True,
                data={'results': results} if results else None
            )
            
        except Exception as e:
            logger.error(f"Webhook processing error: {e}", exc_info=True)
            return WebhookResponse(
                success=False,
                status_code=500,
                message=f"Processing error: {str(e)}"
            ) 