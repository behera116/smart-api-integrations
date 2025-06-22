#!/usr/bin/env python3
"""
Generate Client Command

Generates a dedicated client class file from a provider configuration.
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Dict, Any

import yaml


def register_command(subparsers):
    """Register the generate-client command."""
    parser = subparsers.add_parser(
        'generate-client',
        help='Generate a dedicated client class from provider configuration',
        description='Generate a standalone client class file for easier integration'
    )
    
    parser.add_argument(
        'provider',
        help='Name of the provider to generate client for'
    )
    
    parser.add_argument(
        '--output-file',
        '-o',
        help='Output file path for the generated client class',
        default=None
    )
    
    parser.add_argument(
        '--class-name',
        '-c',
        help='Name for the generated client class',
        default=None
    )
    
    parser.add_argument(
        '--providers-dir',
        help='Directory containing provider configurations',
        default=os.environ.get('SMART_API_INTEGRATIONS_PROVIDERS_DIR', './providers')
    )
    
    parser.set_defaults(func=command_handler)


def command_handler(args) -> int:
    """Handle the generate-client command."""
    try:
        provider_name = args.provider
        providers_dir = Path(args.providers_dir)
        config_path = providers_dir / provider_name / "config.yaml"
        
        # Check if provider config exists
        if not config_path.exists():
            print(f"❌ Provider configuration not found: {config_path}")
            print(f"Available providers: {list_available_providers(providers_dir)}")
            return 1
        
        # Load provider configuration
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Generate class name
        class_name = args.class_name or f"{provider_name.title()}APIClient"
        
        # Generate output file path
        if args.output_file:
            output_file = Path(args.output_file)
        else:
            output_file = Path(f"./{provider_name}_client.py")
        
        # Generate the client class
        client_code = generate_client_class(config, class_name, provider_name)
        
        # Write to file
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            f.write(client_code)
        
        print(f"✅ Generated client class: {output_file}")
        print(f"   Class name: {class_name}")
        print(f"   Provider: {provider_name}")
        print(f"   Endpoints: {len(config.get('endpoints', {}))}")
        
        # Show usage example
        print(f"\n📖 Usage example:")
        print(f"```python")
        print(f"from {output_file.stem} import {class_name}")
        print(f"")
        print(f"client = {class_name}()")
        
        # Show a few method examples
        endpoints = config.get('endpoints', {})
        for i, (endpoint_name, endpoint_config) in enumerate(endpoints.items()):
            if i >= 3:  # Show max 3 examples
                break
            
            method = endpoint_config.get('method', 'GET').upper()
            params = endpoint_config.get('parameters', {})
            
            # Generate example parameters
            example_params = []
            for param_name, param_config in params.items():
                if isinstance(param_config, dict):
                    param_type = param_config.get('type', 'string')
                    required = param_config.get('required', False)
                    
                    if required:
                        if param_type == 'string':
                            example_params.append(f"{param_name}='example'")
                        elif param_type == 'integer':
                            example_params.append(f"{param_name}=123")
                        elif param_type == 'boolean':
                            example_params.append(f"{param_name}=True")
            
            param_str = ', '.join(example_params)
            print(f"result = client.{endpoint_name}({param_str})")
        
        print(f"```")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error generating client: {e}")
        return 1


def generate_auth_initialization(config: Dict[str, Any], provider_name: str) -> list:
    """Generate authentication initialization code based on auth type."""
    auth_config = config.get('auth', {})
    auth_type = auth_config.get('type', 'bearer_token')
    
    lines = [
        '        # Set default authentication from environment if not provided'
    ]
    
    if auth_type == 'bearer_token':
        env_var = f"{provider_name.upper()}_TOKEN"
        lines.extend([
            f'        if \'token_value\' not in auth_overrides:',
            f'            token = os.getenv(\'{env_var}\')',
            f'            if token:',
            f'                auth_overrides[\'token_value\'] = token',
            f'            else:',
            f'                raise ValueError("{provider_name} token required. Set {env_var} environment variable or pass token_value.")'
        ])
    elif auth_type == 'api_key':
        env_var = f"{provider_name.upper()}_API_KEY"
        lines.extend([
            f'        if \'api_key_value\' not in auth_overrides:',
            f'            api_key = os.getenv(\'{env_var}\')',
            f'            if api_key:',
            f'                auth_overrides[\'api_key_value\'] = api_key',
            f'            else:',
            f'                raise ValueError("{provider_name} API key required. Set {env_var} environment variable or pass api_key_value.")'
        ])
    elif auth_type == 'basic':
        username_env = f"{provider_name.upper()}_USERNAME"
        password_env = f"{provider_name.upper()}_PASSWORD"
        lines.extend([
            f'        if \'username\' not in auth_overrides or \'password\' not in auth_overrides:',
            f'            username = auth_overrides.get(\'username\') or os.getenv(\'{username_env}\')',
            f'            password = auth_overrides.get(\'password\') or os.getenv(\'{password_env}\')',
            f'            if username and password:',
            f'                auth_overrides[\'username\'] = username',
            f'                auth_overrides[\'password\'] = password',
            f'            else:',
            f'                raise ValueError("{provider_name} credentials required. Set {username_env} and {password_env} environment variables or pass username/password.")'
        ])
    elif auth_type == 'oauth2':
        client_id_env = f"{provider_name.upper()}_CLIENT_ID"
        client_secret_env = f"{provider_name.upper()}_CLIENT_SECRET"
        lines.extend([
            f'        if \'oauth2_client_id\' not in auth_overrides or \'oauth2_client_secret\' not in auth_overrides:',
            f'            client_id = auth_overrides.get(\'oauth2_client_id\') or os.getenv(\'{client_id_env}\')',
            f'            client_secret = auth_overrides.get(\'oauth2_client_secret\') or os.getenv(\'{client_secret_env}\')',
            f'            if client_id and client_secret:',
            f'                auth_overrides[\'oauth2_client_id\'] = client_id',
            f'                auth_overrides[\'oauth2_client_secret\'] = client_secret',
            f'            else:',
            f'                raise ValueError("{provider_name} OAuth2 credentials required. Set {client_id_env} and {client_secret_env} environment variables.")'
        ])
    elif auth_type == 'jwt':
        env_var = f"{provider_name.upper()}_JWT_TOKEN"
        lines.extend([
            f'        if \'jwt_token\' not in auth_overrides:',
            f'            jwt_token = os.getenv(\'{env_var}\')',
            f'            if jwt_token:',
            f'                auth_overrides[\'jwt_token\'] = jwt_token',
            f'            else:',
            f'                raise ValueError("{provider_name} JWT token required. Set {env_var} environment variable or pass jwt_token.")'
        ])
    
    return lines


def generate_client_class(config: Dict[str, Any], class_name: str, provider_name: str) -> str:
    """Generate the client class code."""
    
    endpoints = config.get('endpoints', {})
    base_url = config.get('base_url', '')
    description = config.get('description', f'{provider_name} API Client')
    
    # Start building the class
    code_lines = [
        '#!/usr/bin/env python3',
        '"""',
        f'Generated {class_name} for {provider_name} API',
        '',
        f'This file was auto-generated by smart-api-integrations.',
        f'Provider: {provider_name}',
        f'Base URL: {base_url}',
        f'Description: {description}',
        '"""',
        '',
        'import os',
        'from typing import Optional, Dict, Any',
        'from smart_api_integrations.clients.universal import UniversalAPIClient',
        'from smart_api_integrations.core.schema import APIResponse',
        '',
        '',
        f'class {class_name}(UniversalAPIClient):',
        f'    """',
        f'    {description}',
        f'    ',
        f'    Auto-generated client for {provider_name} API.',
        f'    Base URL: {base_url}',
        f'    """',
        '',
        '    def __init__(self, **auth_overrides):',
        f'        """',
        f'        Initialize the {provider_name} API client.',
        f'        ',
        f'        Args:',
        f'            **auth_overrides: Authentication overrides',
        f'                            If not provided, reads from environment variables',
        f'        """',
    ] + generate_auth_initialization(config, provider_name) + [
        f'        super().__init__(\'{provider_name}\', **auth_overrides)',
        '',
    ]
    
    # Add methods for each endpoint
    for endpoint_name, endpoint_config in endpoints.items():
        method_code = generate_endpoint_method(endpoint_name, endpoint_config)
        code_lines.extend(method_code)
        code_lines.append('')
    
    # Add utility methods
    code_lines.extend([
        '    def list_available_methods(self) -> Dict[str, str]:',
        '        """List all available API methods."""',
        '        return {',
    ])
    
    for endpoint_name, endpoint_config in endpoints.items():
        description = endpoint_config.get('description', f'{endpoint_name} endpoint')
        code_lines.append(f'            \'{endpoint_name}\': {repr(description)},')
    
    code_lines.extend([
        '        }',
        '',
        '    def get_method_help(self, method_name: str) -> str:',
        '        """Get help for a specific method."""',
        '        if hasattr(self, method_name):',
        '            method = getattr(self, method_name)',
        '            return method.__doc__ or f"No documentation available for {method_name}"',
        '        else:',
        '            return f"Method {method_name} not found"',
    ])
    
    return '\n'.join(code_lines)


def generate_endpoint_method(endpoint_name: str, endpoint_config: Dict[str, Any]) -> list:
    """Generate code for a single endpoint method."""
    
    method = endpoint_config.get('method', 'GET').upper()
    path = endpoint_config.get('path', '')
    description = endpoint_config.get('description', f'{endpoint_name} endpoint')
    parameters = endpoint_config.get('parameters', {})
    
    # Build method signature
    method_params = ['self']
    docstring_params = []
    
    # Separate parameters by location
    path_params = []
    query_params = []
    body_params = []
    
    for param_name, param_config in parameters.items():
        if isinstance(param_config, dict):
            param_type = param_config.get('type', 'string')
            required = param_config.get('required', False)
            location = param_config.get('in', 'query')
            param_description = param_config.get('description', '')
            
            # Convert type
            python_type = 'str'
            if param_type == 'integer':
                python_type = 'int'
            elif param_type == 'boolean':
                python_type = 'bool'
            elif param_type == 'array':
                python_type = 'list'
            elif param_type == 'object':
                python_type = 'dict'
            
            # Add to method signature
            if required:
                method_params.append(f'{param_name}: {python_type}')
            else:
                method_params.append(f'{param_name}: Optional[{python_type}] = None')
            
            # Add to docstring
            required_str = 'required' if required else 'optional'
            docstring_params.append(f'        {param_name} ({python_type}, {required_str}): {param_description}')
            
            # Categorize by location
            if location == 'path':
                path_params.append(param_name)
            elif location in ['body', 'form']:
                body_params.append(param_name)
            else:  # query, header
                query_params.append(param_name)
    
    # Build method signature
    signature = f'def {endpoint_name}({", ".join(method_params)}) -> APIResponse:'
    
    # Build docstring
    docstring_lines = [
        f'        """',
        f'        {description}',
        f'        ',
        f'        {method} {path}',
    ]
    
    if docstring_params:
        docstring_lines.extend([
            f'        ',
            f'        Args:',
        ] + docstring_params)
    
    docstring_lines.extend([
        f'        ',
        f'        Returns:',
        f'            APIResponse: The API response object',
        f'        """'
    ])
    
    # Build method body
    body_lines = []
    
    # Prepare parameters
    if path_params or query_params or body_params:
        body_lines.append('        # Prepare parameters')
        
        if path_params or query_params:
            body_lines.append('        params = {}')
            for param in path_params + query_params:
                body_lines.append(f'        if {param} is not None:')
                body_lines.append(f'            params[\'{param}\'] = {param}')
        
        if body_params:
            body_lines.append('        json_data = {}')
            for param in body_params:
                body_lines.append(f'        if {param} is not None:')
                body_lines.append(f'            json_data[\'{param}\'] = {param}')
        
        body_lines.append('')
    
    # Make the API call
    call_params = [f"'{endpoint_name}'"]
    
    if path_params or query_params:
        call_params.append('params=params')
    
    if body_params:
        call_params.append('json_data=json_data')
    
    body_lines.append(f'        return self._smart_client.call_endpoint({", ".join(call_params)})')
    
    # Combine everything
    method_lines = [
        f'    {signature}',
    ] + docstring_lines + body_lines
    
    return method_lines


def list_available_providers(providers_dir: Path) -> list:
    """List available providers in the providers directory."""
    if not providers_dir.exists():
        return []
    
    providers = []
    for item in providers_dir.iterdir():
        if item.is_dir() and (item / "config.yaml").exists():
            providers.append(item.name)
    
    return sorted(providers)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Generate a dedicated client class from provider configuration'
    )
    register_command(parser.add_subparsers())
    args = parser.parse_args()
    
    if hasattr(args, 'func'):
        sys.exit(args.func(args))
    else:
        parser.print_help()
        sys.exit(1) 