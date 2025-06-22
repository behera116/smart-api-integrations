"""
Universal API Client - Minimal implementation for method-based API access with static typing.
Synchronous implementation for simplicity.
"""

import os
import inspect
from typing import Any, Dict, Optional, Protocol, runtime_checkable, Callable
from ..core.schema import APIResponse


@runtime_checkable
class APIMethod(Protocol):
    """Protocol for API methods - provides static typing for dynamic methods."""
    
    def __call__(self, **kwargs: Any) -> APIResponse:
        """Call the API method with keyword arguments."""
        ...


class UniversalAPIClient:
    """
    Universal API Client that provides method-based access to APIs.
    
    Dynamically creates methods from provider endpoints with parameter validation and static typing.
    Example: client.get_user() instead of client.call_endpoint('get_user')
    """
    
    # Override in subclasses to define method mappings
    METHOD_MAPPING: Dict[str, str] = {}
    
    def __init__(self, provider_name: str, **auth_overrides):
        """Initialize the client with a provider."""
        from ..core.registry import get_client
        self._smart_client = get_client(provider_name, **auth_overrides)
        self.provider_name = provider_name
        self._config = getattr(self._smart_client, 'config', None)
        self._method_cache: Dict[str, APIMethod] = {}
    
    def _get_endpoint_config(self, endpoint_name: str) -> Optional[Dict]:
        """Get configuration for a specific endpoint."""
        if self._config and hasattr(self._config, 'endpoints') and self._config.endpoints:
            return self._config.endpoints.get(endpoint_name)
        return None
    
    def _validate_and_prepare_kwargs(self, endpoint_name: str, **kwargs) -> Dict[str, Any]:
        """
        Validate and prepare kwargs based on endpoint configuration.
        
        Helps developers use the right parameter names (json_data vs params vs data).
        """
        endpoint_config = self._get_endpoint_config(endpoint_name)
        if not endpoint_config:
            # No config available, pass through as-is
            return kwargs
        
        # Get endpoint method and path for context
        method = getattr(endpoint_config, 'method', 'GET').upper()
        path = getattr(endpoint_config, 'path', '')
        
        # Prepare the final kwargs
        final_kwargs = kwargs.copy()
        
        # Auto-convert common parameter patterns
        if 'json' in kwargs and 'json_data' not in kwargs:
            final_kwargs['json_data'] = kwargs.pop('json')
        
        if 'body' in kwargs and method in ['POST', 'PUT', 'PATCH']:
            if 'json_data' not in final_kwargs and 'data' not in final_kwargs:
                # Try to determine if it's JSON or plain data
                body = kwargs.pop('body')
                if isinstance(body, (dict, list)):
                    final_kwargs['json_data'] = body
                else:
                    final_kwargs['data'] = body
        
        # Handle direct parameter passing - if parameters are passed directly as kwargs,
        # group them into the appropriate dictionaries
        if hasattr(endpoint_config, 'parameters') and endpoint_config.parameters:
            params_dict = final_kwargs.get('params', {})
            json_data_dict = final_kwargs.get('json_data', {})
            
            # Check for direct parameter passing
            for param_name, param_config in endpoint_config.parameters.items():
                if param_name in final_kwargs and param_name not in ['params', 'json_data', 'data', 'headers']:
                    # Handle both dict and object parameter configurations
                    if isinstance(param_config, dict):
                        param_location = param_config.get('in', 'query')
                    else:
                        param_location = getattr(param_config, 'in', 'query')
                    
                    param_value = final_kwargs.pop(param_name)
                    
                    if param_location == 'body':
                        json_data_dict[param_name] = param_value
                    else:
                        # For path and query parameters
                        params_dict[param_name] = param_value
            
            if params_dict:
                final_kwargs['params'] = params_dict
            if json_data_dict:
                final_kwargs['json_data'] = json_data_dict
        
        # Validate required parameters if defined in config
        if hasattr(endpoint_config, 'parameters'):
            self._validate_required_params(endpoint_name, endpoint_config.parameters, final_kwargs)
        
        return final_kwargs
    
    def _validate_required_params(self, endpoint_name: str, param_config: Dict, kwargs: Dict):
        """Validate required parameters based on endpoint configuration."""
        if not param_config:
            return
        
        missing_params = []
        for param_name, param_def in param_config.items():
            # Handle both dict and object parameter definitions
            if hasattr(param_def, 'required'):
                required = param_def.required
                param_location = getattr(param_def, 'in', 'query')
            elif isinstance(param_def, dict):
                required = param_def.get('required', False)
                param_location = param_def.get('in', 'query')
            else:
                required = False
                param_location = 'query'
            
            if required:
                # Check if required param is provided in any form
                if param_location == 'query' and 'params' in kwargs:
                    if param_name not in kwargs['params']:
                        missing_params.append(f"{param_name} (in params)")
                elif param_location == 'path':
                    if 'params' not in kwargs or param_name not in kwargs['params']:
                        missing_params.append(f"{param_name} (in path)")
                elif param_location == 'body':
                    if 'json_data' not in kwargs and 'data' not in kwargs:
                        missing_params.append(f"{param_name} (in body)")
        
        if missing_params:
            raise ValueError(f"Missing required parameters for {endpoint_name}: {', '.join(missing_params)}")
    
    def _get_method_help(self, endpoint_name: str) -> str:
        """Generate helpful documentation for a method based on config."""
        endpoint_config = self._get_endpoint_config(endpoint_name)
        if not endpoint_config:
            return f"Call the '{endpoint_name}' endpoint"
        
        method = getattr(endpoint_config, 'method', 'GET')
        path = getattr(endpoint_config, 'path', '')
        description = getattr(endpoint_config, 'description', '')
        
        help_text = f"{method} {path}"
        if description:
            help_text += f" - {description}"
        
        # Add parameter information
        if hasattr(endpoint_config, 'parameters') and endpoint_config.parameters:
            help_text += "\n\nParameters:"
            for param_name, param_def in endpoint_config.parameters.items():
                # Handle both dict and object parameter definitions
                if hasattr(param_def, 'type'):
                    param_type = param_def.type
                    param_location = getattr(param_def, 'in', 'query')
                    required = getattr(param_def, 'required', False)
                    param_desc = getattr(param_def, 'description', '')
                elif isinstance(param_def, dict):
                    param_type = param_def.get('type', 'string')
                    param_location = param_def.get('in', 'query')
                    required = param_def.get('required', False)
                    param_desc = param_def.get('description', '')
                else:
                    param_type = 'string'
                    param_location = 'query'
                    required = False
                    param_desc = ''
                
                req_text = " (required)" if required else ""
                help_text += f"\n  - {param_name} ({param_type}, in {param_location}){req_text}"
                if param_desc:
                    help_text += f": {param_desc}"
        
        # Add usage examples
        if method in ['POST', 'PUT', 'PATCH']:
            help_text += f"\n\nUsage: client.{endpoint_name}(json_data={{...}}, params={{...}})"
        else:
            help_text += f"\n\nUsage: client.{endpoint_name}(params={{...}})"
        
        return help_text
    
    def _create_typed_method(self, endpoint_name: str) -> APIMethod:
        """Create a typed method for an endpoint."""
        def dynamic_method(**kwargs: Any) -> APIResponse:
            # Validate and prepare parameters
            validated_kwargs = self._validate_and_prepare_kwargs(endpoint_name, **kwargs)
            return self._smart_client.call_endpoint(endpoint_name, **validated_kwargs)
        
        # Add helpful documentation
        dynamic_method.__name__ = endpoint_name
        dynamic_method.__doc__ = self._get_method_help(endpoint_name)
        dynamic_method.__annotations__ = {'return': APIResponse}
        
        return dynamic_method
    
    def __getattr__(self, name: str) -> APIMethod:
        """
        Dynamically create methods for API endpoints with validation and typing.
        
        First checks METHOD_MAPPING, then falls back to direct endpoint name.
        Returns a properly typed method that IDEs can understand.
        """
        # Check cache first
        if name in self._method_cache:
            return self._method_cache[name]
        
        # Check if method is mapped to a specific endpoint
        endpoint_name = self.METHOD_MAPPING.get(name, name)
        
        # Create the typed method
        method = self._create_typed_method(endpoint_name)
        
        # Cache it for future use
        self._method_cache[name] = method
        
        return method
    
    def get_method_help(self, method_name: str) -> str:
        """Get help documentation for a specific method."""
        endpoint_name = self.METHOD_MAPPING.get(method_name, method_name)
        return self._get_method_help(endpoint_name)
    
    def list_available_methods(self) -> Dict[str, str]:
        """List all available methods with their descriptions."""
        methods = {}
        
        if self._config and hasattr(self._config, 'endpoints') and self._config.endpoints:
            for endpoint_name in self._config.endpoints.keys():
                # Check if there's a mapped method name
                method_name = endpoint_name
                for mapped_name, mapped_endpoint in self.METHOD_MAPPING.items():
                    if mapped_endpoint == endpoint_name:
                        method_name = mapped_name
                        break
                
                endpoint_config = self._config.endpoints[endpoint_name]
                description = getattr(endpoint_config, 'description', f"Call {endpoint_name} endpoint")
                methods[method_name] = description
        
        return methods
    
    def call_raw(self, method: str, path: str, **kwargs: Any) -> APIResponse:
        """Make a raw API call."""
        return self._smart_client.call_raw(method, path, **kwargs)
    
    def close(self) -> None:
        """Close the underlying client."""
        if hasattr(self._smart_client, 'close'):
            self._smart_client.close()
    
    def __enter__(self) -> 'UniversalAPIClient':
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close() 