"""
Response adapter for standardizing API responses across different providers.
"""

import json
import time
from typing import Any, Dict, Optional

import httpx
from .schema import APIResponse


class ResponseAdapter:
    """Adapts raw HTTP responses to standardized APIResponse format."""
    
    def __init__(self, provider_name: Optional[str] = None):
        self.provider_name = provider_name
    
    def adapt_response(
        self,
        response: httpx.Response,
        endpoint_name: Optional[str] = None,
        start_time: Optional[float] = None,
        retry_count: int = 0
    ) -> APIResponse:
        """Convert an httpx.Response to standardized APIResponse."""
        execution_time = None
        if start_time:
            execution_time = time.time() - start_time
        
        headers = dict(response.headers) if response.headers else None
        
        # Success response
        if 200 <= response.status_code < 300:
            return APIResponse.success_response(
                data=self._parse_response_data(response),
                status_code=response.status_code,
                headers=headers,
                provider=self.provider_name,
                endpoint=endpoint_name,
                execution_time=execution_time
            )
        
        # Error response
        error_message = self._extract_error_message(response)
        error_details = self._extract_error_details(response)
        
        return APIResponse.error_response(
            error=error_message,
            status_code=response.status_code,
            error_details=error_details,
            headers=headers,
            provider=self.provider_name,
            endpoint=endpoint_name,
            execution_time=execution_time,
            retry_count=retry_count
        )
    
    def adapt_response_exception(
        self,
        exception: Exception,
        endpoint_name: Optional[str] = None,
        execution_time: Optional[float] = None,
        retry_count: int = 0
    ) -> APIResponse:
        """Convert an exception to standardized APIResponse."""
        error_message = str(exception)
        status_code = 0
        
        # Map specific exception types to appropriate status codes
        if isinstance(exception, httpx.TimeoutException):
            status_code = 408
            error_message = "Request timeout"
        elif isinstance(exception, httpx.ConnectError):
            status_code = 503
            error_message = "Service unavailable - connection error"
        elif isinstance(exception, httpx.HTTPStatusError):
            status_code = exception.response.status_code
            error_message = f"HTTP {status_code}: {exception.response.text}"
        
        error_details = {
            "exception_type": type(exception).__name__,
            "exception_message": str(exception)
        }
        
        return APIResponse.error_response(
            error=error_message,
            status_code=status_code,
            error_details=error_details,
            provider=self.provider_name,
            endpoint=endpoint_name,
            execution_time=execution_time,
            retry_count=retry_count
        )
    
    def _parse_response_data(self, response: httpx.Response) -> Any:
        """Parse response data based on content type."""
        content_type = response.headers.get("content-type", "").lower()
        
        if "application/json" in content_type:
            try:
                return response.json()
            except json.JSONDecodeError:
                return response.text
        elif "text/" in content_type:
            return response.text
        elif "application/xml" in content_type:
            # Could add XML parsing here if needed
            return response.text
        else:
            # For binary content, return info about the content
            return {
                "content_type": content_type,
                "content_length": len(response.content),
                "content": response.content if len(response.content) < 1024 else None
            }
    
    def _extract_error_message(self, response: httpx.Response) -> str:
        """Extract error message from response."""
        try:
            # Try to parse JSON error response
            if "application/json" in response.headers.get("content-type", ""):
                error_data = response.json()
                
                # Common error message fields
                for field in ["error", "message", "error_description", "detail", "msg"]:
                    if field in error_data:
                        return str(error_data[field])
                
                # If no standard field, return the whole JSON as string
                return json.dumps(error_data)
            
            # Fallback to response text
            return response.text or f"HTTP {response.status_code} Error"
        
        except Exception:
            return f"HTTP {response.status_code} Error"
    
    def _extract_error_details(self, response: httpx.Response) -> Optional[Dict[str, Any]]:
        """Extract additional error details from response."""
        try:
            if "application/json" in response.headers.get("content-type", ""):
                return response.json()
            else:
                return {"response_text": response.text}
        except Exception:
            return None


class ProviderResponseAdapter(ResponseAdapter):
    """Provider-specific response adapter for custom response handling."""
    
    def __init__(self, provider_name: str, custom_adapters: Optional[Dict[str, callable]] = None):
        super().__init__(provider_name)
        self.custom_adapters = custom_adapters or {}
    
    def adapt_response(
        self,
        response: httpx.Response,
        endpoint_name: Optional[str] = None,
        start_time: Optional[float] = None,
        retry_count: int = 0
    ) -> APIResponse:
        """Apply custom adapter if available, otherwise use default."""
        
        if endpoint_name and endpoint_name in self.custom_adapters:
            custom_adapter = self.custom_adapters[endpoint_name]
            try:
                return custom_adapter(response, endpoint_name, start_time, retry_count)
            except Exception as e:
                # Fall back to default adapter if custom adapter fails
                print(f"Custom adapter failed for {endpoint_name}: {e}")
        
        return super().adapt_response(response, endpoint_name, start_time, retry_count)
        
    def adapt_response_exception(
        self,
        exception: Exception,
        endpoint_name: Optional[str] = None,
        execution_time: Optional[float] = None,
        retry_count: int = 0
    ) -> APIResponse:
        """Apply custom exception adapter if available, otherwise use default."""
        
        if endpoint_name and endpoint_name in self.custom_adapters:
            custom_adapter = self.custom_adapters.get(f"{endpoint_name}_exception")
            if custom_adapter:
                try:
                    return custom_adapter(exception, endpoint_name, execution_time, retry_count)
                except Exception as e:
                    # Fall back to default adapter if custom adapter fails
                    print(f"Custom exception adapter failed for {endpoint_name}: {e}")
        
        return super().adapt_response_exception(exception, endpoint_name, execution_time, retry_count) 