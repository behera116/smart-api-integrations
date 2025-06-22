"""
Pydantic schemas for Smart API system configuration and validation.
"""

from typing import Any, Dict, List, Optional, Union
from enum import Enum
import time
from pydantic import BaseModel, Field, validator
import httpx


class AuthType(str, Enum):
    """Supported authentication types."""
    API_KEY = "api_key"
    BEARER_TOKEN = "bearer_token"
    OAUTH2 = "oauth2"
    JWT = "jwt"
    BASIC = "basic"
    NONE = "none"


class HTTPMethod(str, Enum):
    """Supported HTTP methods."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class RateLimitConfig(BaseModel):
    """Rate limiting configuration."""
    requests_per_second: Optional[float] = None
    requests_per_minute: Optional[int] = None
    requests_per_hour: Optional[int] = None
    burst_limit: Optional[int] = None


class RetryConfig(BaseModel):
    """Retry strategy configuration."""
    max_retries: int = 3
    backoff_factor: float = 0.3
    retry_on_status: List[int] = Field(default_factory=lambda: [429, 500, 502, 503, 504])
    retry_on_exceptions: List[str] = Field(default_factory=lambda: ["httpx.TimeoutException", "httpx.ConnectError"])


class AuthConfig(BaseModel):
    """Authentication configuration."""
    type: AuthType
    api_key_header: Optional[str] = None
    api_key_param: Optional[str] = None
    api_key_value: Optional[str] = None
    token_value: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    oauth2_client_id: Optional[str] = None
    oauth2_client_secret: Optional[str] = None
    oauth2_token_url: Optional[str] = None
    oauth2_scopes: Optional[List[str]] = None
    jwt_token: Optional[str] = None
    jwt_algorithm: Optional[str] = "HS256"
    # Cache configuration for OAuth tokens
    cache_tokens: bool = True
    token_cache_key: Optional[str] = None


class EndpointConfig(BaseModel):
    """Configuration for individual API endpoints."""
    path: str
    method: HTTPMethod = HTTPMethod.GET
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None
    body_schema: Optional[Dict[str, Any]] = None
    response_schema: Optional[Dict[str, Any]] = None
    timeout: Optional[float] = None
    rate_limit: Optional[RateLimitConfig] = None
    retry: Optional[RetryConfig] = None


class ProviderConfig(BaseModel):
    """Configuration for API providers."""
    name: str
    base_url: str
    description: Optional[str] = None
    version: Optional[str] = "1.0"
    auth: AuthConfig
    default_headers: Optional[Dict[str, str]] = None
    default_timeout: float = 30.0
    rate_limit: Optional[RateLimitConfig] = None
    retry: Optional[RetryConfig] = None
    endpoints: Dict[str, EndpointConfig] = Field(default_factory=dict)
    openapi_spec_url: Optional[str] = None
    use_openapi_client: bool = False

    @validator('base_url')
    def validate_base_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('base_url must start with http:// or https://')
        return v.rstrip('/')

    @validator('endpoints')
    def validate_endpoints(cls, v):
        if not v:
            return v
        for endpoint_name, endpoint_config in v.items():
            if not endpoint_config.path.startswith('/'):
                endpoint_config.path = '/' + endpoint_config.path
        return v


class APIResponse(BaseModel):
    """Standardized API response wrapper."""
    success: bool
    status_code: int
    data: Optional[Any] = None
    error: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None
    provider: Optional[str] = None
    endpoint: Optional[str] = None
    execution_time: Optional[float] = None
    retry_count: Optional[int] = 0

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def success_response(
        cls,
        data: Any,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        provider: Optional[str] = None,
        endpoint: Optional[str] = None,
        execution_time: Optional[float] = None
    ) -> "APIResponse":
        """Create a successful API response."""
        return cls(
            success=True,
            status_code=status_code,
            data=data,
            headers=headers,
            provider=provider,
            endpoint=endpoint,
            execution_time=execution_time
        )

    @classmethod
    def error_response(
        cls,
        error: str,
        status_code: int = 500,
        error_details: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        provider: Optional[str] = None,
        endpoint: Optional[str] = None,
        execution_time: Optional[float] = None,
        retry_count: int = 0
    ) -> "APIResponse":
        """Create an error API response."""
        return cls(
            success=False,
            status_code=status_code,
            error=error,
            error_details=error_details,
            headers=headers,
            provider=provider,
            endpoint=endpoint,
            execution_time=execution_time,
            retry_count=retry_count
        )


class TokenCache(BaseModel):
    """OAuth token cache model."""
    access_token: str
    token_type: str = "Bearer"
    expires_in: Optional[int] = None
    refresh_token: Optional[str] = None
    scope: Optional[str] = None
    created_at: float = Field(default_factory=time.time)

    def is_expired(self, buffer_seconds: int = 300) -> bool:
        """Check if token is expired (with buffer)."""
        if not self.expires_in:
            return False
        return (time.time() - self.created_at) >= (self.expires_in - buffer_seconds)