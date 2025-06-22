"""
Command to add new API providers to Smart API system.
Creates provider configuration with basic setup and optional client generation.

Usage: 
    smart-api-integrations add-provider --name stripe --base-url "https://api.stripe.com/v1"
    smart-api-integrations add-provider --interactive
    smart-api-integrations add-provider --name github --template rest-api --auth bearer
"""

import os
import sys
import yaml
import re
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, List

# Predefined templates for common API patterns
TEMPLATES = {
    'rest-api': {
        'description': 'Standard REST API with JSON responses',
        'default_headers': {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        'default_timeout': 30.0,
        'sample_endpoints': {
            'health_check': {
                'path': '/health',
                'method': 'GET',
                'description': 'API health check'
            }
        }
    },
    'graphql': {
        'description': 'GraphQL API endpoint',
        'default_headers': {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        'default_timeout': 30.0,
        'sample_endpoints': {
            'graphql_query': {
                'path': '/graphql',
                'method': 'POST',
                'description': 'GraphQL query endpoint'
            }
        }
    },
    'webhook': {
        'description': 'Webhook-based API for event handling',
        'default_headers': {
            'Accept': 'application/json'
        },
        'default_timeout': 30.0,
        'sample_endpoints': {
            'webhook_endpoint': {
                'path': '/webhook',
                'method': 'POST',
                'description': 'Webhook receiver endpoint'
            }
        }
    }
}

# Authentication type configurations
AUTH_TYPES = {
    'none': {
        'type': 'none',
        'description': 'No authentication required'
    },
    'api-key': {
        'type': 'api_key',
        'description': 'API Key authentication',
        'fields': ['api_key_header', 'api_key_value']
    },
    'bearer': {
        'type': 'bearer_token',
        'description': 'Bearer token authentication',
        'fields': ['token_value']
    },
    'basic': {
        'type': 'basic',
        'description': 'Basic authentication (username/password)',
        'fields': ['username', 'password']
    },
    'oauth2': {
        'type': 'oauth2',
        'description': 'OAuth2 client credentials flow',
        'fields': ['oauth2_client_id', 'oauth2_client_secret', 'oauth2_token_url', 'oauth2_scopes']
    },
    'jwt': {
        'type': 'jwt',
        'description': 'JWT token authentication',
        'fields': ['jwt_token', 'jwt_algorithm']
    }
}


def register_command(subparsers):
    """Register the command with the given subparsers."""
    parser = subparsers.add_parser(
        'add-provider',
        help='Add new API provider with configuration setup',
        description='Add new API provider to Smart API system with configuration setup'
    )
    
    parser.add_argument(
        '--name',
        type=str,
        help='Provider name (e.g., stripe, github, hubspot)'
    )
    parser.add_argument(
        '--base-url',
        type=str,
        help='Base URL for the API (e.g., https://api.stripe.com/v1)'
    )
    parser.add_argument(
        '--description',
        type=str,
        help='Description of the API provider'
    )
    parser.add_argument(
        '--auth',
        choices=list(AUTH_TYPES.keys()),
        help='Authentication type'
    )
    parser.add_argument(
        '--template',
        choices=list(TEMPLATES.keys()),
        default='rest-api',
        help='API template to use (default: rest-api)'
    )
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Interactive mode with prompts'
    )
    parser.add_argument(
        '--create-client',
        action='store_true',
        help='Create Python client class file'
    )
    parser.add_argument(
        '--overwrite',
        action='store_true',
        help='Overwrite existing provider configuration'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be created without making changes'
    )
    parser.add_argument(
        '--providers-dir',
        type=str,
        default=os.environ.get('SMART_API_INTEGRATIONS_PROVIDERS_DIR', './providers'),
        help='Directory containing provider configurations'
    )
    
    parser.set_defaults(func=command_handler)
    return parser

def command_handler(args):
    """Handle the add-provider command."""
    try:
        if args.interactive:
            provider_config = interactive_setup()
        else:
            provider_config = non_interactive_setup(args)
        
        # Validate configuration
        validate_config(provider_config)
        
        # Display configuration
        display_config(provider_config)
        
        if args.dry_run:
            print("Dry run completed. No files were created.")
            return 0
        
        # Confirm creation
        if not confirm_creation(provider_config):
            print("Operation cancelled.")
            return 0
        
        # Create provider
        create_provider(provider_config, args)
        
        # Show next steps
        show_next_steps(provider_config)
        
        return 0
    except Exception as e:
        print(f"Error creating provider: {str(e)}")
        return 1


def interactive_setup() -> Dict[str, Any]:
    """Interactive setup with prompts."""
    print("=== Smart API Provider Setup ===")
    print("")
    
    # Basic information
    name = prompt_input("Provider name", required=True, validator=validate_provider_name)
    base_url = prompt_input("Base URL", required=True, validator=validate_url)
    description = prompt_input("Description", default=f"{name.title()} API integration")
    version = prompt_input("API Version", default="1.0")
    
    # Template selection
    print("\n📋 Available templates:")
    for template_name, template_config in TEMPLATES.items():
        print(f"  {template_name}: {template_config['description']}")
    
    template = prompt_choice("Template", list(TEMPLATES.keys()), default='rest-api')
    
    # Authentication setup
    print("\n🔐 Authentication setup:")
    print("Available authentication types:")
    for auth_name, auth_config in AUTH_TYPES.items():
        print(f"  {auth_name}: {auth_config['description']}")
    
    auth_type = prompt_choice("Authentication type", list(AUTH_TYPES.keys()), default='bearer')
    auth_config = setup_auth_interactive(auth_type)
    
    # Rate limiting setup
    has_rate_limit = prompt_yes_no("\nDoes this API have rate limits?", default=False)
    rate_limit = setup_rate_limit_interactive() if has_rate_limit else None
    
    # Compile configuration
    config = {
        'name': name,
        'base_url': base_url,
        'description': description,
        'version': version,
        'auth': auth_config,
        'endpoints': TEMPLATES[template]['sample_endpoints'].copy(),
        'default_headers': TEMPLATES[template]['default_headers'].copy(),
        'default_timeout': TEMPLATES[template]['default_timeout']
    }
    
    if rate_limit:
        config['rate_limit'] = rate_limit
    
    return config

def non_interactive_setup(args) -> Dict[str, Any]:
    """Non-interactive setup from command line arguments."""
    if not args.name:
        raise ValueError("Provider name is required in non-interactive mode. Use --name option.")
    
    if not args.base_url:
        raise ValueError("Base URL is required in non-interactive mode. Use --base-url option.")
    
    # Validate inputs
    name = validate_provider_name(args.name)
    base_url = validate_url(args.base_url)
    
    # Get template
    template = args.template or 'rest-api'
    
    # Get auth config
    auth_type = args.auth or 'none'
    auth_config = get_auth_config(auth_type)
    
    # Compile configuration
    config = {
        'name': name,
        'base_url': base_url,
        'description': args.description or f"{name.title()} API integration",
        'version': '1.0',
        'auth': auth_config,
        'endpoints': TEMPLATES[template]['sample_endpoints'].copy(),
        'default_headers': TEMPLATES[template]['default_headers'].copy(),
        'default_timeout': TEMPLATES[template]['default_timeout']
    }
    
    return config


def setup_auth_interactive(auth_type: str) -> Dict[str, Any]:
    """Interactive setup for authentication configuration."""
    auth_config = {'type': AUTH_TYPES[auth_type]['type']}
    
    # Skip if no fields needed
    if auth_type == 'none':
        return auth_config
    
    # Get required fields
    fields = AUTH_TYPES[auth_type]['fields']
    
    for field in fields:
        # Special handling for different field types
        if field == 'api_key_header':
            value = prompt_input("API key header name", default="X-API-Key")
        elif field == 'api_key_value':
            value = prompt_input("API key value (or env var)", default="${API_KEY}")
        elif field == 'token_value':
            provider_env = prompt_input("Environment variable for token", default="TOKEN")
            value = f"${{{provider_env}}}"
        elif field == 'username':
            value = prompt_input("Username (or env var)", default="${API_USERNAME}")
        elif field == 'password':
            value = prompt_input("Password (or env var)", default="${API_PASSWORD}")
        elif field == 'oauth2_client_id':
            value = prompt_input("OAuth2 client ID (or env var)", default="${CLIENT_ID}")
        elif field == 'oauth2_client_secret':
            value = prompt_input("OAuth2 client secret (or env var)", default="${CLIENT_SECRET}")
        elif field == 'oauth2_token_url':
            value = prompt_input("OAuth2 token URL", required=True)
        elif field == 'oauth2_scopes':
            scopes_str = prompt_input("OAuth2 scopes (comma-separated)", default="")
            value = [s.strip() for s in scopes_str.split(',')] if scopes_str else None
        elif field == 'jwt_token':
            value = prompt_input("JWT token (or env var)", default="${JWT_TOKEN}")
        elif field == 'jwt_algorithm':
            value = prompt_input("JWT algorithm", default="HS256")
        else:
            value = prompt_input(f"{field}")
        
        if value is not None:  # Skip None values
            auth_config[field] = value
    
    return auth_config

def setup_rate_limit_interactive() -> Dict[str, Any]:
    """Interactive setup for rate limiting configuration."""
    print("\n⏱ Rate limiting setup:")
    
    rate_limit_type = prompt_choice(
        "Rate limit type",
        ['requests_per_second', 'requests_per_minute', 'requests_per_hour'],
        default='requests_per_minute'
    )
    
    if rate_limit_type == 'requests_per_second':
        value = prompt_input("Requests per second", default="10", validator=validate_float)
        return {'requests_per_second': float(value)}
    elif rate_limit_type == 'requests_per_minute':
        value = prompt_input("Requests per minute", default="60", validator=validate_int)
        return {'requests_per_minute': int(value)}
    else:  # requests_per_hour
        value = prompt_input("Requests per hour", default="1000", validator=validate_int)
        return {'requests_per_hour': int(value)}


def get_auth_config(auth_type: str) -> Dict[str, Any]:
    """Get basic authentication configuration for the given type."""
    auth_config = {'type': AUTH_TYPES[auth_type]['type']}
    
    # Add default values for required fields
    if auth_type == 'api-key':
        auth_config['api_key_header'] = 'X-API-Key'
        auth_config['api_key_value'] = '${API_KEY}'
    elif auth_type == 'bearer':
        auth_config['token_value'] = '${API_TOKEN}'
    elif auth_type == 'basic':
        auth_config['username'] = '${API_USERNAME}'
        auth_config['password'] = '${API_PASSWORD}'
    elif auth_type == 'oauth2':
        auth_config['oauth2_client_id'] = '${CLIENT_ID}'
        auth_config['oauth2_client_secret'] = '${CLIENT_SECRET}'
        auth_config['oauth2_token_url'] = 'https://api.example.com/oauth/token'
    elif auth_type == 'jwt':
        auth_config['jwt_token'] = '${JWT_TOKEN}'
        auth_config['jwt_algorithm'] = 'HS256'
    
    return auth_config


def validate_config(config: Dict[str, Any]):
    """Validate the provider configuration."""
    required_fields = ['name', 'base_url', 'auth']
    
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate URL format
    if not config['base_url'].startswith(('http://', 'https://')):
        raise ValueError("Base URL must start with http:// or https://")


def display_config(config: Dict[str, Any]):
    """Display the provider configuration."""
    print("\n=== Provider Configuration ===")
    print(yaml.dump(config, default_flow_style=False, sort_keys=False))


def confirm_creation(config: Dict[str, Any]) -> bool:
    """Ask user to confirm provider creation."""
    return prompt_yes_no(f"\nCreate provider '{config['name']}' with the above configuration?", default=True)

def create_provider(config: Dict[str, Any], args):
    """Create the provider configuration files."""
    # Get provider directory path
    providers_dir = args.providers_dir
    provider_path = get_provider_path(config['name'], providers_dir)
    
    # Check if provider already exists
    if provider_path.exists() and not args.overwrite:
        raise ValueError(f"Provider '{config['name']}' already exists. Use --overwrite to replace it.")
    
    # Create provider directory
    provider_path.mkdir(parents=True, exist_ok=True)
    
    # Create config file
    config_path = provider_path / "config.yaml"
    create_config_file(config, config_path)
    
    # Create client file if requested
    if args.create_client:
        client_path = get_client_path(config['name'])
        create_client_file(config, client_path)


def create_config_file(config: Dict[str, Any], config_path: Path):
    """Create the provider configuration YAML file."""
    # Write config to file
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    print(f"✅ Created provider configuration: {config_path}")


def create_client_file(config: Dict[str, Any], client_path: Path):
    """Create a Python client class file for the provider."""
    provider_name = config['name']
    class_name = ''.join(word.capitalize() for word in provider_name.split('_')) + 'APIClient'
    
    # Create client directory if it doesn't exist
    client_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Client file template
    client_template = f'''"""
{provider_name.title()} API Client for Smart API Integrations.

This file was auto-generated by smart-api-integrations add-provider command.
"""

from typing import Dict, Any, Optional, List

from smart_api_integrations.clients.universal import UniversalAPIClient


class {class_name}(UniversalAPIClient):
    """
    {provider_name.title()} API Client
    
    {config.get('description', '')}
    
    Base URL: {config.get('base_url', '')}
    """
    
    # Method name mapping for better IDE support
    METHOD_MAPPING = {{
        # Map method names to endpoint names for better IDE support
        # Example: 'get_user': 'get_user'
    }}
    
    def __init__(self, **auth_overrides):
        """Initialize the {provider_name.title()} API client."""
        super().__init__('{provider_name}', **auth_overrides)
    
    # Add custom methods here
'''
    
    # Write client file
    with open(client_path, 'w', encoding='utf-8') as f:
        f.write(client_template)
    
    print(f"✅ Created client class: {client_path}")

def show_next_steps(config: Dict[str, Any]):
    """Show next steps after provider creation."""
    provider_name = config['name']
    
    print("\n=== Next Steps ===")
    
    # Show environment variable setup
    print("\n1. Set up environment variables:")
    
    auth_config = config.get('auth', {})
    auth_type = auth_config.get('type')
    
    if auth_type == 'api_key':
        env_var = auth_config.get('api_key_value', '${API_KEY}')
        if env_var.startswith('${') and env_var.endswith('}'):
            env_name = env_var[2:-1]
            print(f"   export {env_name}=\"your-api-key\"")
    
    elif auth_type == 'bearer_token':
        env_var = auth_config.get('token_value', '${API_TOKEN}')
        if env_var.startswith('${') and env_var.endswith('}'):
            env_name = env_var[2:-1]
            print(f"   export {env_name}=\"your-bearer-token\"")
    
    elif auth_type == 'basic':
        username_var = auth_config.get('username', '${API_USERNAME}')
        password_var = auth_config.get('password', '${API_PASSWORD}')
        
        if username_var.startswith('${') and username_var.endswith('}'):
            username_env = username_var[2:-1]
            print(f"   export {username_env}=\"your-username\"")
        
        if password_var.startswith('${') and password_var.endswith('}'):
            password_env = password_var[2:-1]
            print(f"   export {password_env}=\"your-password\"")
    
    # Show usage example
    print("\n2. Use the client in your code:")
    print(f"""
   ```python
   from smart_api_integrations import SmartAPIClient
   
   # Initialize client
   {provider_name} = SmartAPIClient('{provider_name}')
   
   # Make API calls
   response = {provider_name}.health_check()
   print(f"API Status: {{response.success}}")
   ```
   """)
    
    # Show next command for adding endpoints
    print("\n3. Add more endpoints to your provider:")
    print(f"   smart-api-integrations add-endpoints --provider {provider_name}")
    
    print("\n✨ Provider setup complete! ✨")


def get_provider_path(provider_name: str, providers_dir: str) -> Path:
    """Get the path to the provider directory."""
    return Path(providers_dir) / provider_name


def get_client_path(provider_name: str) -> Path:
    """Get the path to the client file."""
    # Determine the package path
    package_path = Path(__file__).parent.parent.parent
    return package_path / "clients" / f"{provider_name}.py"


def validate_provider_name(name: str) -> str:
    """Validate provider name format."""
    if not re.match(r'^[a-z][a-z0-9_]*$', name):
        raise ValueError("Provider name must start with a letter and contain only lowercase letters, numbers, and underscores")
    return name


def validate_url(url: str) -> str:
    """Validate URL format."""
    if not url.startswith(('http://', 'https://')):
        raise ValueError("URL must start with http:// or https://")
    return url


def validate_float(value: str) -> str:
    """Validate float value."""
    try:
        float(value)
        return value
    except ValueError:
        raise ValueError(f"Invalid float value: {value}")


def validate_int(value: str) -> str:
    """Validate integer value."""
    try:
        int(value)
        return value
    except ValueError:
        raise ValueError(f"Invalid integer value: {value}")

def prompt_input(prompt: str, default: str = None, required: bool = False, validator=None) -> str:
    """Prompt for user input with validation."""
    prompt_text = f"{prompt}"
    if default:
        prompt_text += f" [{default}]"
    prompt_text += ": "
    
    while True:
        value = input(prompt_text)
        
        if not value and default is not None:
            value = default
        
        if not value and required:
            print("This field is required.")
            continue
        
        if not value and not required:
            return None
        
        if validator:
            try:
                value = validator(value)
            except ValueError as e:
                print(f"Error: {e}")
                continue
        
        return value


def prompt_choice(prompt: str, choices: List[str], default: str = None) -> str:
    """Prompt for a choice from a list of options."""
    if default and default not in choices:
        raise ValueError(f"Default value '{default}' not in choices: {choices}")
    
    print(f"{prompt}:")
    for i, choice in enumerate(choices, 1):
        print(f"  {i}. {choice}" + (" (default)" if choice == default else ""))
    
    while True:
        value = input(f"Enter choice (1-{len(choices)}): ")
        
        if not value and default:
            return default
        
        try:
            index = int(value) - 1
            if 0 <= index < len(choices):
                return choices[index]
        except ValueError:
            pass
        
        print(f"Please enter a number between 1 and {len(choices)}.")


def prompt_yes_no(prompt: str, default: bool = None) -> bool:
    """Prompt for a yes/no answer."""
    default_text = " [Y/n]" if default is True else " [y/N]" if default is False else " [y/n]"
    prompt_text = f"{prompt}{default_text}: "
    
    while True:
        value = input(prompt_text).lower()
        
        if not value and default is not None:
            return default
        
        if value in ('y', 'yes'):
            return True
        elif value in ('n', 'no'):
            return False
        
        print("Please enter 'y' or 'n'.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Add new API provider to Smart API system')
    register_command(parser.add_subparsers())
    args = parser.parse_args()
    
    if hasattr(args, 'func'):
        sys.exit(args.func(args))
    else:
        parser.print_help()
        sys.exit(1)
