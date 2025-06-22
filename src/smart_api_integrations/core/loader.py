"""
Configuration loader for Smart API system.
Loads and parses provider YAML configs and OpenAPI specifications.
Synchronous implementation for simplicity.
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from urllib.parse import urljoin
from string import Template

import httpx
from .schema import ProviderConfig, EndpointConfig, AuthConfig, HTTPMethod, AuthType


class ConfigLoader:
    """Loads and parses provider configurations."""
    
    def __init__(self, providers_directory: Optional[str] = None):
        if providers_directory:
            self.providers_directory = Path(providers_directory)
        else:
            # Check environment variable first
            env_providers_dir = os.environ.get('SMART_API_INTEGRATIONS_PROVIDERS_DIR')
            if env_providers_dir:
                self.providers_directory = Path(env_providers_dir)
            else:
                # Default to providers directory within the package
                current_dir = Path(__file__).parent.parent
                self.providers_directory = current_dir / "providers"
    
    def _resolve_env_vars(self, value: Any) -> Any:
        """Resolve environment variables in configuration values."""
        if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
            # Extract environment variable name
            env_var = value[2:-1]
            return os.environ.get(env_var, value)
        elif isinstance(value, str):
            # Use Template for multiple variables
            template = Template(value)
            return template.safe_substitute(os.environ)
        elif isinstance(value, dict):
            return {k: self._resolve_env_vars(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._resolve_env_vars(item) for item in value]
        return value
    
    def load_provider_config(self, provider_name: str) -> ProviderConfig:
        """Load configuration for a specific provider."""
        provider_dir = self.providers_directory / provider_name
        
        if not provider_dir.exists():
            raise ValueError(f"Provider directory not found: {provider_dir}")
        
        # Try to load config.yaml first
        config_file = provider_dir / "config.yaml"
        if config_file.exists():
            return self._load_yaml_config(config_file, provider_name)
        
        # Try openapi.yaml
        openapi_file = provider_dir / "openapi.yaml"
        if openapi_file.exists():
            return self._load_openapi_config(openapi_file, provider_name)
        
        # Try openapi.json
        openapi_json_file = provider_dir / "openapi.json"
        if openapi_json_file.exists():
            return self._load_openapi_json_config(openapi_json_file, provider_name)
        
        raise ValueError(f"No configuration file found for provider: {provider_name}")
    
    def list_available_providers(self) -> List[str]:
        """List all available providers."""
        if not self.providers_directory.exists():
            return []
        
        providers = []
        for item in self.providers_directory.iterdir():
            if item.is_dir():
                # Check if it has any configuration files
                has_config = any([
                    (item / "config.yaml").exists(),
                    (item / "openapi.yaml").exists(),
                    (item / "openapi.json").exists()
                ])
                if has_config:
                    providers.append(item.name)
        
        return sorted(providers)
    
    def _load_yaml_config(self, config_file: Path, provider_name: str) -> ProviderConfig:
        """Load provider configuration from YAML file."""
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        # Resolve environment variables in the config
        config_data = self._resolve_env_vars(config_data)
        
        # Process auth configuration
        auth_data = config_data.get('auth', {})
        auth_config = self._process_auth_config(auth_data)
        
        # Process endpoints
        endpoints = {}
        endpoints_data = config_data.get('endpoints', {})
        for endpoint_name, endpoint_data in endpoints_data.items():
            endpoints[endpoint_name] = self._process_endpoint_config(endpoint_data)
        
        return ProviderConfig(
            name=provider_name,
            base_url=config_data['base_url'],
            description=config_data.get('description'),
            version=config_data.get('version', '1.0'),
            auth=auth_config,
            default_headers=config_data.get('default_headers'),
            default_timeout=config_data.get('default_timeout', 30.0),
            endpoints=endpoints,
            openapi_spec_url=config_data.get('openapi_spec_url'),
            use_openapi_client=config_data.get('use_openapi_client', False)
        )
    
    def _load_openapi_config(self, openapi_file: Path, provider_name: str) -> ProviderConfig:
        """Load provider configuration from OpenAPI YAML spec."""
        with open(openapi_file, 'r', encoding='utf-8') as f:
            openapi_spec = yaml.safe_load(f)
        
        return self._process_openapi_spec(openapi_spec, provider_name)
    
    def _load_openapi_json_config(self, openapi_file: Path, provider_name: str) -> ProviderConfig:
        """Load provider configuration from OpenAPI JSON spec."""
        with open(openapi_file, 'r', encoding='utf-8') as f:
            openapi_spec = json.load(f)
        
        return self._process_openapi_spec(openapi_spec, provider_name)
    
    def load_remote_openapi_config(self, provider_name: str, openapi_url: str) -> ProviderConfig:
        """Load provider configuration from remote OpenAPI spec."""
        with httpx.Client() as client:
            response = client.get(openapi_url)
            response.raise_for_status()
            
            if openapi_url.endswith('.json'):
                openapi_spec = response.json()
            else:
                openapi_spec = yaml.safe_load(response.text)
        
        return self._process_openapi_spec(openapi_spec, provider_name)
    
    def _process_openapi_spec(self, openapi_spec: Dict[str, Any], provider_name: str) -> ProviderConfig:
        """Process OpenAPI specification into ProviderConfig."""
        info = openapi_spec.get('info', {})
        servers = openapi_spec.get('servers', [])
        
        # Get base URL from servers
        base_url = servers[0]['url'] if servers else 'https://api.example.com'
        
        # Extract security schemes for auth
        auth_config = self._extract_auth_from_openapi(openapi_spec)
        
        # Process paths to endpoints
        endpoints = {}
        paths = openapi_spec.get('paths', {})
        for path, path_item in paths.items():
            for method, operation in path_item.items():
                if method.upper() not in [m.value for m in HTTPMethod]:
                    continue
                
                operation_id = operation.get('operationId', f"{method}_{path.replace('/', '_')}")
                endpoints[operation_id] = EndpointConfig(
                    path=path,
                    method=HTTPMethod(method.upper()),
                    description=operation.get('summary', operation.get('description')),
                    parameters=self._extract_parameters_from_openapi(operation),
                    body_schema=self._extract_request_body_from_openapi(operation),
                    response_schema=self._extract_responses_from_openapi(operation)
                )
        
        return ProviderConfig(
            name=provider_name,
            base_url=base_url,
            description=info.get('description'),
            version=info.get('version', '1.0'),
            auth=auth_config,
            endpoints=endpoints,
            use_openapi_client=True
        )
    
    def _process_auth_config(self, auth_data: Dict[str, Any]) -> AuthConfig:
        """Process authentication configuration."""
        auth_type = AuthType(auth_data.get('type', 'none'))
        
        # Resolve environment variables in auth values
        auth_data = self._resolve_env_vars(auth_data)
        
        return AuthConfig(
            type=auth_type,
            api_key_header=auth_data.get('api_key_header'),
            api_key_param=auth_data.get('api_key_param'),
            api_key_value=auth_data.get('api_key_value'),
            token_value=auth_data.get('token_value'),
            username=auth_data.get('username'),
            password=auth_data.get('password'),
            oauth2_client_id=auth_data.get('oauth2_client_id'),
            oauth2_client_secret=auth_data.get('oauth2_client_secret'),
            oauth2_token_url=auth_data.get('oauth2_token_url'),
            oauth2_scopes=auth_data.get('oauth2_scopes'),
            jwt_token=auth_data.get('jwt_token'),
            jwt_algorithm=auth_data.get('jwt_algorithm', 'HS256'),
            cache_tokens=auth_data.get('cache_tokens', True),
            token_cache_key=auth_data.get('token_cache_key')
        )
    
    def _process_endpoint_config(self, endpoint_data: Dict[str, Any]) -> EndpointConfig:
        """Process endpoint configuration."""
        return EndpointConfig(
            path=endpoint_data['path'],
            method=HTTPMethod(endpoint_data.get('method', 'GET').upper()),
            description=endpoint_data.get('description'),
            parameters=endpoint_data.get('parameters'),
            headers=endpoint_data.get('headers'),
            body_schema=endpoint_data.get('body_schema'),
            response_schema=endpoint_data.get('response_schema'),
            timeout=endpoint_data.get('timeout')
        )
    
    def _extract_auth_from_openapi(self, openapi_spec: Dict[str, Any]) -> AuthConfig:
        """Extract authentication configuration from OpenAPI spec."""
        components = openapi_spec.get('components', {})
        security_schemes = components.get('securitySchemes', {})
        
        # Default to no auth
        if not security_schemes:
            return AuthConfig(type=AuthType.NONE)
        
        # Take the first security scheme
        scheme_name, scheme = next(iter(security_schemes.items()))
        scheme_type = scheme.get('type', '').lower()
        
        if scheme_type == 'apikey':
            in_location = scheme.get('in', 'header')
            name = scheme.get('name', 'X-API-Key')
            
            if in_location == 'header':
                return AuthConfig(type=AuthType.API_KEY, api_key_header=name)
            else:
                return AuthConfig(type=AuthType.API_KEY, api_key_param=name)
        
        elif scheme_type == 'http':
            if scheme.get('scheme') == 'bearer':
                return AuthConfig(type=AuthType.BEARER_TOKEN)
            elif scheme.get('scheme') == 'basic':
                return AuthConfig(type=AuthType.BASIC)
        
        elif scheme_type == 'oauth2':
            flows = scheme.get('flows', {})
            if 'clientCredentials' in flows:
                flow = flows['clientCredentials']
                return AuthConfig(
                    type=AuthType.OAUTH2,
                    oauth2_token_url=flow.get('tokenUrl'),
                    oauth2_scopes=list(flow.get('scopes', {}).keys())
                )
        
        return AuthConfig(type=AuthType.NONE)
    
    def _extract_parameters_from_openapi(self, operation: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract parameters from OpenAPI operation."""
        parameters = operation.get('parameters', [])
        if not parameters:
            return None
        
        param_schemas = {}
        for param in parameters:
            param_name = param.get('name')
            param_schema = param.get('schema', {})
            param_schemas[param_name] = {
                'type': param_schema.get('type'),
                'description': param.get('description'),
                'required': param.get('required', False),
                'in': param.get('in')  # query, header, path, cookie
            }
        
        return param_schemas
    
    def _extract_request_body_from_openapi(self, operation: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract request body schema from OpenAPI operation."""
        request_body = operation.get('requestBody')
        if not request_body:
            return None
        
        content = request_body.get('content', {})
        # Prefer JSON content
        for content_type in ['application/json', 'application/x-www-form-urlencoded']:
            if content_type in content:
                return content[content_type].get('schema')
        
        return None
    
    def _extract_responses_from_openapi(self, operation: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract response schemas from OpenAPI operation."""
        responses = operation.get('responses', {})
        if not responses:
            return None
        
        # Extract successful response schema (200, 201, etc.)
        for status_code in ['200', '201', '202']:
            if status_code in responses:
                response = responses[status_code]
                content = response.get('content', {})
                if 'application/json' in content:
                    return content['application/json'].get('schema')
        
        return None 