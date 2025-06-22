"""
Webhook schema definitions for Smart API webhook system.
"""

from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime


class WebhookVerificationType(Enum):
    """Types of webhook signature verification."""
    HMAC_SHA256 = "hmac_sha256"
    HMAC_SHA1 = "hmac_sha1"
    RSA = "rsa"
    CUSTOM = "custom"
    NONE = "none"


@dataclass
class WebhookConfig:
    """Configuration for a webhook endpoint."""
    path: str
    verify_signature: bool = True
    signing_secret_env: Optional[str] = None
    verification_type: WebhookVerificationType = WebhookVerificationType.HMAC_SHA256
    signature_header: str = "X-Signature"
    timestamp_header: Optional[str] = None
    replay_tolerance: int = 300  # 5 minutes
    events: List[str] = None
    rate_limit: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.events is None:
            self.events = []


@dataclass
class WebhookEvent:
    """Standardized webhook event."""
    id: str
    type: str
    provider: str
    webhook_name: str
    payload: Dict[str, Any]
    headers: Dict[str, str]
    timestamp: datetime
    verified: bool = False
    signature: Optional[str] = None
    raw_body: Optional[bytes] = None


@dataclass
class WebhookResponse:
    """Standardized webhook response."""
    success: bool
    status_code: int = 200
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    
    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response."""
        result = {
            'success': self.success,
            'status_code': self.status_code
        }
        if self.message:
            result['message'] = self.message
        if self.data:
            result['data'] = self.data
        return result


@dataclass
class WebhookProviderConfig:
    """Provider-specific webhook configuration."""
    name: str
    webhooks: Dict[str, WebhookConfig]
    default_verification_type: WebhookVerificationType = WebhookVerificationType.HMAC_SHA256
    default_signature_header: str = "X-Signature"
    default_timestamp_header: Optional[str] = None
    ip_whitelist: Optional[List[str]] = None
    
    def get_webhook(self, name: str = 'default') -> Optional[WebhookConfig]:
        """Get webhook configuration by name."""
        return self.webhooks.get(name) 