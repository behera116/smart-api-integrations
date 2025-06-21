"""
Universal dynamic API client for Smart API system.
Supports rate limiting, retries, and flexible authentication.
Synchronous implementation for simplicity.
"""

import time
from typing import Any, Dict, Optional
from urllib.parse import urljoin

import httpx
from pydantic import ValidationError

from .schema import ProviderConfig, EndpointConfig, APIResponse, RateLimitConfig, RetryConfig
from .auth import AuthResolverFactory
from .response_adapter import ResponseAdapter


class RateLimiter:
    """Rate limiter implementation."""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.requests = []
    
    def acquire(self):
        """Acquire permission to make a request."""
        now = time.time()
        
        # Clean old requests
        if self.config.requests_per_second:
            cutoff = now - 1.0
            self.requests = [req_time for req_time in self.requests if req_time > cutoff]
            
            if len(self.requests) >= self.config.requests_per_second:
                sleep_time = 1.0 - (now - min(self.requests))
                if sleep_time > 0:
                    time.sleep(sleep_time)
        
        elif self.config.requests_per_minute:
            cutoff = now - 60.0
            self.requests = [req_time for req_time in self.requests if req_time > cutoff]
            
            if len(self.requests) >= self.config.requests_per_minute:
                sleep_time = 60.0 - (now - min(self.requests))
                if sleep_time > 0:
                    time.sleep(sleep_time)
        
        elif self.config.requests_per_hour:
            cutoff = now - 3600.0
            self.requests = [req_time for req_time in self.requests if req_time > cutoff]
            
            if len(self.requests) >= self.config.requests_per_hour:
                sleep_time = 3600.0 - (now - min(self.requests))
                if sleep_time > 0:
                    time.sleep(sleep_time)
        
        self.requests.append(now)


class SmartAPIClient:
    """Universal dynamic API client."""
    
    def __init__(self, config: ProviderConfig):
        self.config = config
        self.auth_resolver = AuthResolverFactory.create_resolver(config.auth)
        self.response_adapter = ResponseAdapter(config.name)
        
        # Initialize rate limiter if configured
        self.rate_limiter = None
        if config.rate_limit:
            self.rate_limiter = RateLimiter(config.rate_limit)
        
        # Initialize HTTP client
        self.client = httpx.Client(
            timeout=config.default_timeout,
            headers=config.default_headers or {}
        )
    
    def call_endpoint(
        self,
        endpoint_name: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> APIResponse:
        """Call a configured endpoint."""
        
        if endpoint_name not in self.config.endpoints:
            return APIResponse.error_response(
                error=f"Endpoint '{endpoint_name}' not found",
                status_code=404,
                provider=self.config.name,
                endpoint=endpoint_name
            )
        
        endpoint_config = self.config.endpoints[endpoint_name]
        return self._make_request(
            endpoint_config=endpoint_config,
            endpoint_name=endpoint_name,
            params=params,
            json_data=json_data,
            data=data,
            headers=headers,
            timeout=timeout
        )
    
    def call_raw(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> APIResponse:
        """Make a raw API call."""
        
        # Create temporary endpoint config
        endpoint_config = EndpointConfig(
            path=path,
            method=method.upper()
        )
        
        return self._make_request(
            endpoint_config=endpoint_config,
            endpoint_name=f"{method.upper()}_{path}",
            params=params,
            json_data=json_data,
            data=data,
            headers=headers,
            timeout=timeout
        )
    
    def _make_request(
        self,
        endpoint_config: EndpointConfig,
        endpoint_name: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> APIResponse:
        """Make HTTP request with retries and rate limiting."""
        
        # Use endpoint-specific or provider-level retry config
        retry_config = endpoint_config.retry or self.config.retry or RetryConfig()
        
        # Use endpoint-specific or provider-level rate limiter
        rate_limiter = None
        if endpoint_config.rate_limit:
            rate_limiter = RateLimiter(endpoint_config.rate_limit)
        else:
            rate_limiter = self.rate_limiter
        
        last_exception = None
        start_time = time.time()
        
        for attempt in range(retry_config.max_retries + 1):
            try:
                # Apply rate limiting
                if rate_limiter:
                    rate_limiter.acquire()
                
                # Build URL
                url = urljoin(self.config.base_url, endpoint_config.path.lstrip('/'))
                
                # Merge headers
                request_headers = {}
                if self.config.default_headers:
                    request_headers.update(self.config.default_headers)
                if endpoint_config.headers:
                    request_headers.update(endpoint_config.headers)
                if headers:
                    request_headers.update(headers)
                
                # Create request
                request = httpx.Request(
                    method=endpoint_config.method.value,
                    url=url,
                    params=params,
                    json=json_data,
                    data=data,
                    headers=request_headers
                )
                
                # Apply authentication
                request = self.auth_resolver.apply_auth(request)
                
                # Validate request body if schema provided
                if endpoint_config.body_schema and json_data:
                    self._validate_data(json_data, endpoint_config.body_schema)
                
                # Make the request
                response = self.client.send(request, timeout=timeout or self.config.default_timeout)
                
                # Validate response if schema provided
                if endpoint_config.response_schema and response.status_code < 400:
                    response_data = response.json()
                    self._validate_data(response_data, endpoint_config.response_schema)
                
                # Convert to APIResponse
                execution_time = time.time() - start_time
                return self.response_adapter.adapt_response(
                    response, endpoint_name, execution_time, attempt
                )
                
            except Exception as e:
                last_exception = e
                
                if not self._should_retry(e, retry_config, attempt):
                    break
                
                if attempt < retry_config.max_retries:
                    sleep_time = retry_config.backoff_factor * (2 ** attempt)
                    time.sleep(sleep_time)
        
        # All retries failed
        execution_time = time.time() - start_time
        return self.response_adapter.adapt_response_exception(
            last_exception, endpoint_name, execution_time, retry_config.max_retries
        )
    
    def _should_retry(self, exception: Exception, retry_config: RetryConfig, attempt: int) -> bool:
        """Determine if we should retry the request."""
        if attempt >= retry_config.max_retries:
            return False
        
        # Check if exception type should be retried
        exception_name = exception.__class__.__name__
        if retry_config.retry_on_exceptions and exception_name in retry_config.retry_on_exceptions:
            return True
        
        # Check if HTTP status should be retried
        if hasattr(exception, 'response') and hasattr(exception.response, 'status_code'):
            if retry_config.retry_on_status and exception.response.status_code in retry_config.retry_on_status:
                return True
        
        return False
    
    def _validate_data(self, data: Dict[str, Any], schema: Dict[str, Any]):
        """Validate data against schema."""
        try:
            # Simple validation for now
            for field, field_schema in schema.items():
                if field in data:
                    if field_schema.get('type') == 'string' and not isinstance(data[field], str):
                        raise ValidationError(f"Field '{field}' should be a string")
                    elif field_schema.get('type') == 'integer' and not isinstance(data[field], int):
                        raise ValidationError(f"Field '{field}' should be an integer")
                    elif field_schema.get('type') == 'boolean' and not isinstance(data[field], bool):
                        raise ValidationError(f"Field '{field}' should be a boolean")
                    elif field_schema.get('type') == 'object' and not isinstance(data[field], dict):
                        raise ValidationError(f"Field '{field}' should be an object")
                    elif field_schema.get('type') == 'array' and not isinstance(data[field], list):
                        raise ValidationError(f"Field '{field}' should be an array")
                elif field_schema.get('required', False):
                    raise ValidationError(f"Required field '{field}' is missing")
        except Exception as e:
            print(f"Validation error: {e}")
            # Continue anyway for now
    
    def close(self):
        """Close the client."""
        self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
