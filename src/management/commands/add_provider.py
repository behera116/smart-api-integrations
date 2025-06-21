"""
Django management command to add new API providers to Smart API system.
Creates provider configuration with basic setup and optional client generation.

Usage: 
    python manage.py add_provider --name stripe --base-url "https://api.stripe.com/v1"
    python manage.py add_provider --interactive
    python manage.py add_provider --name github --template rest-api --auth bearer
"""

import os
import yaml
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


class Command(BaseCommand):
    help = 'Add new API provider to Smart API system with configuration setup'
    
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
    
    def add_arguments(self, parser):
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
            choices=list(self.AUTH_TYPES.keys()),
            help='Authentication type'
        )
        parser.add_argument(
            '--template',
            choices=list(self.TEMPLATES.keys()),
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
    
    def handle(self, *args, **options):
        try:
            if options['interactive']:
                provider_config = self.interactive_setup()
            else:
                provider_config = self.non_interactive_setup(options)
            
            # Validate configuration
            self.validate_config(provider_config)
            
            # Display configuration
            self.display_config(provider_config)
            
            if options['dry_run']:
                self.stdout.write(self.style.SUCCESS("Dry run completed. No files were created."))
                return
            
            # Confirm creation
            if not self.confirm_creation(provider_config):
                self.stdout.write("Operation cancelled.")
                return
            
            # Create provider
            self.create_provider(provider_config, options)
            
            # Show next steps
            self.show_next_steps(provider_config)
            
        except Exception as e:
            raise CommandError(f"Error creating provider: {str(e)}")
    
    def interactive_setup(self) -> Dict[str, Any]:
        """Interactive setup with prompts."""
        self.stdout.write(self.style.SUCCESS("=== Smart API Provider Setup ==="))
        self.stdout.write("")
        
        # Basic information
        name = self.prompt_input("Provider name", required=True, validator=self.validate_provider_name)
        base_url = self.prompt_input("Base URL", required=True, validator=self.validate_url)
        description = self.prompt_input("Description", default=f"{name.title()} API integration")
        version = self.prompt_input("API Version", default="1.0")
        
        # Template selection
        self.stdout.write("\n📋 Available templates:")
        for template_name, template_config in self.TEMPLATES.items():
            self.stdout.write(f"  {template_name}: {template_config['description']}")
        
        template = self.prompt_choice("Template", list(self.TEMPLATES.keys()), default='rest-api')
        
        # Authentication setup
        self.stdout.write("\n🔐 Authentication setup:")
        for auth_name, auth_config in self.AUTH_TYPES.items():
            self.stdout.write(f"  {auth_name}: {auth_config['description']}")
        
        auth_type = self.prompt_choice("Authentication type", list(self.AUTH_TYPES.keys()), default='bearer')
        auth_config = self.setup_auth_interactive(auth_type)
        
        # Advanced options
        self.stdout.write("\n⚙️ Advanced options:")
        timeout = self.prompt_input("Default timeout (seconds)", default="30.0", validator=self.validate_float)
        
        # Rate limiting
        setup_rate_limit = self.prompt_yes_no("Configure rate limiting?", default=False)
        rate_limit_config = None
        if setup_rate_limit:
            rate_limit_config = self.setup_rate_limit_interactive()
        
        # Headers
        setup_headers = self.prompt_yes_no("Configure default headers?", default=True)
        headers_config = {}
        if setup_headers:
            template_config = self.TEMPLATES[template]
            headers_config = template_config.get('default_headers', {}).copy()
            
            # Allow custom headers
            while True:
                add_header = self.prompt_yes_no("Add custom header?", default=False)
                if not add_header:
                    break
                
                header_name = self.prompt_input("Header name", required=True)
                header_value = self.prompt_input("Header value", required=True)
                headers_config[header_name] = header_value
        
        # Build configuration
        config = {
            'name': name,
            'base_url': base_url,
            'description': description,
            'version': version,
            'auth': auth_config,
            'default_timeout': float(timeout),
            'template': template
        }
        
        if headers_config:
            config['default_headers'] = headers_config
        
        if rate_limit_config:
            config['rate_limit'] = rate_limit_config
        
        return config
    
    def non_interactive_setup(self, options) -> Dict[str, Any]:
        """Non-interactive setup from command line arguments."""
        name = options.get('name')
        base_url = options.get('base_url')
        
        if not name:
            raise CommandError("Provider name is required. Use --name or --interactive")
        
        if not base_url:
            raise CommandError("Base URL is required. Use --base-url or --interactive")
        
        # Validate inputs
        self.validate_provider_name(name)
        self.validate_url(base_url)
        
        template = options.get('template', 'rest-api')
        auth_type = options.get('auth', 'bearer')
        
        # Build basic configuration
        config = {
            'name': name,
            'base_url': base_url,
            'description': options.get('description') or f"{name.title()} API integration",
            'version': "1.0",
            'auth': self.get_auth_config(auth_type),
            'default_timeout': 30.0,
            'template': template
        }
        
        # Add template defaults
        template_config = self.TEMPLATES[template]
        if 'default_headers' in template_config:
            config['default_headers'] = template_config['default_headers']
        
        return config
    
    def setup_auth_interactive(self, auth_type: str) -> Dict[str, Any]:
        """Interactive authentication setup."""
        auth_config = self.AUTH_TYPES[auth_type].copy()
        base_config = {'type': auth_config['type']}
        
        if auth_type == 'none':
            return base_config
        
        fields = auth_config.get('fields', [])
        
        for field in fields:
            if field == 'api_key_header':
                value = self.prompt_input("API Key header name", default="X-API-Key")
                base_config['api_key_header'] = value
            elif field == 'api_key_value':
                env_var = f"{base_config.get('name', 'API').upper()}_API_KEY"
                value = self.prompt_input("API Key value", default=f"${{{env_var}}}")
                base_config['api_key_value'] = value
            elif field == 'token_value':
                env_var = f"{base_config.get('name', 'API').upper()}_TOKEN"
                value = self.prompt_input("Bearer token value", default=f"${{{env_var}}}")
                base_config['token_value'] = value
            elif field == 'username':
                env_var = f"{base_config.get('name', 'API').upper()}_USERNAME"
                value = self.prompt_input("Username", default=f"${{{env_var}}}")
                base_config['username'] = value
            elif field == 'password':
                env_var = f"{base_config.get('name', 'API').upper()}_PASSWORD"
                value = self.prompt_input("Password", default=f"${{{env_var}}}")
                base_config['password'] = value
            elif field == 'oauth2_client_id':
                env_var = f"{base_config.get('name', 'API').upper()}_CLIENT_ID"
                value = self.prompt_input("OAuth2 Client ID", default=f"${{{env_var}}}")
                base_config['oauth2_client_id'] = value
            elif field == 'oauth2_client_secret':
                env_var = f"{base_config.get('name', 'API').upper()}_CLIENT_SECRET"
                value = self.prompt_input("OAuth2 Client Secret", default=f"${{{env_var}}}")
                base_config['oauth2_client_secret'] = value
            elif field == 'oauth2_token_url':
                value = self.prompt_input("OAuth2 Token URL", required=True)
                base_config['oauth2_token_url'] = value
            elif field == 'oauth2_scopes':
                scopes_input = self.prompt_input("OAuth2 Scopes (comma-separated)", default="")
                if scopes_input:
                    base_config['oauth2_scopes'] = [s.strip() for s in scopes_input.split(',')]
            elif field == 'jwt_token':
                env_var = f"{base_config.get('name', 'API').upper()}_JWT_TOKEN"
                value = self.prompt_input("JWT Token", default=f"${{{env_var}}}")
                base_config['jwt_token'] = value
            elif field == 'jwt_algorithm':
                value = self.prompt_input("JWT Algorithm", default="HS256")
                base_config['jwt_algorithm'] = value
        
        return base_config
    
    def setup_rate_limit_interactive(self) -> Dict[str, Any]:
        """Interactive rate limit setup."""
        rate_limit = {}
        
        rps = self.prompt_input("Requests per second", validator=self.validate_float)
        if rps:
            rate_limit['requests_per_second'] = float(rps)
        
        rpm = self.prompt_input("Requests per minute", validator=self.validate_int)
        if rpm:
            rate_limit['requests_per_minute'] = int(rpm)
        
        burst = self.prompt_input("Burst limit", validator=self.validate_int)
        if burst:
            rate_limit['burst_limit'] = int(burst)
        
        return rate_limit if rate_limit else None
    
    def get_auth_config(self, auth_type: str) -> Dict[str, Any]:
        """Get basic auth configuration for non-interactive mode."""
        auth_config = self.AUTH_TYPES[auth_type]
        base_config = {'type': auth_config['type']}
        
        if auth_type == 'bearer':
            base_config['token_value'] = "${API_TOKEN}"
        elif auth_type == 'api-key':
            base_config['api_key_header'] = "X-API-Key"
            base_config['api_key_value'] = "${API_KEY}"
        elif auth_type == 'basic':
            base_config['username'] = "${API_USERNAME}"
            base_config['password'] = "${API_PASSWORD}"
        elif auth_type == 'oauth2':
            base_config.update({
                'oauth2_client_id': "${OAUTH2_CLIENT_ID}",
                'oauth2_client_secret': "${OAUTH2_CLIENT_SECRET}",
                'oauth2_token_url': "https://api.example.com/oauth/token"
            })
        elif auth_type == 'jwt':
            base_config['jwt_token'] = "${JWT_TOKEN}"
            base_config['jwt_algorithm'] = "HS256"
        
        return base_config
    
    def validate_config(self, config: Dict[str, Any]):
        """Validate provider configuration."""
        required_fields = ['name', 'base_url', 'description', 'auth']
        
        for field in required_fields:
            if field not in config:
                raise CommandError(f"Missing required field: {field}")
        
        # Check if provider already exists
        provider_path = self.get_provider_path(config['name'])
        if provider_path.exists():
            raise CommandError(
                f"Provider '{config['name']}' already exists at {provider_path}. "
                "Use --overwrite to replace it."
            )
    
    def display_config(self, config: Dict[str, Any]):
        """Display the configuration that will be created."""
        self.stdout.write(self.style.SUCCESS("\n=== Provider Configuration ==="))
        
        # Remove template field for display
        display_config = config.copy()
        template = display_config.pop('template', 'rest-api')
        
        # Add sample endpoints from template
        template_config = self.TEMPLATES[template]
        if 'sample_endpoints' in template_config:
            display_config['endpoints'] = template_config['sample_endpoints']
        
        yaml_output = yaml.dump(display_config, default_flow_style=False, sort_keys=False)
        self.stdout.write(yaml_output)
    
    def confirm_creation(self, config: Dict[str, Any]) -> bool:
        """Ask user to confirm provider creation."""
        self.stdout.write(f"\nCreate provider '{config['name']}'?")
        response = input("Continue? [y/N]: ").strip().lower()
        return response in ['y', 'yes']
    
    def create_provider(self, config: Dict[str, Any], options: Dict[str, Any]):
        """Create the provider configuration and files."""
        provider_name = config['name']
        provider_path = self.get_provider_path(provider_name)
        
        # Create provider directory
        provider_path.mkdir(parents=True, exist_ok=options.get('overwrite', False))
        
        # Create config.yaml
        config_path = provider_path / 'config.yaml'
        self.create_config_file(config, config_path)
        
        # Create client file if requested
        if options.get('create_client', False):
            client_path = self.get_client_path(provider_name)
            self.create_client_file(config, client_path)
        
        self.stdout.write(self.style.SUCCESS(f"✅ Created provider '{provider_name}'"))
        self.stdout.write(f"   Configuration: {config_path}")
        
        if options.get('create_client', False):
            self.stdout.write(f"   Client: {client_path}")
    
    def create_config_file(self, config: Dict[str, Any], config_path: Path):
        """Create the config.yaml file."""
        # Remove template field and add template-specific content
        template = config.pop('template', 'rest-api')
        template_config = self.TEMPLATES[template]
        
        # Add sample endpoints
        if 'sample_endpoints' in template_config:
            config['endpoints'] = template_config['sample_endpoints']
        
        # Add retry configuration
        config['retry'] = {
            'max_retries': 3,
            'backoff_factor': 0.3,
            'retry_on_status': [429, 500, 502, 503, 504]
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    def create_client_file(self, config: Dict[str, Any], client_path: Path):
        """Create the Python client file."""
        provider_name = config['name']
        class_name = f"{provider_name.title()}APIClient"
        
        # Determine auth parameter based on auth type
        auth_type = config['auth']['type']
        if auth_type == 'bearer_token':
            auth_param = 'token_value'
            env_var = f"{provider_name.upper()}_TOKEN"
        elif auth_type == 'api_key':
            auth_param = 'api_key_value'
            env_var = f"{provider_name.upper()}_API_KEY"
        elif auth_type == 'basic':
            auth_param = 'username'
            env_var = f"{provider_name.upper()}_USERNAME"
        else:
            auth_param = 'token_value'
            env_var = f"{provider_name.upper()}_TOKEN"
        
        client_code = f'''"""
{class_name} - Smart API client for {config['description']}
"""

import os
from newfies.smart_api.clients.universal import UniversalAPIClient


class {class_name}(UniversalAPIClient):
    """
    {config['description']}
    
    Usage:
        client = {class_name}()
        response = client.health_check()
    """
    
    def __init__(self, {auth_param}: str = None):
        {auth_param} = {auth_param} or os.getenv('{env_var}')
        if not {auth_param}:
            raise ValueError("{env_var} environment variable is required")
        
        super().__init__('{provider_name}', {auth_param}={auth_param})
'''
        
        with open(client_path, 'w', encoding='utf-8') as f:
            f.write(client_code)
    
    def show_next_steps(self, config: Dict[str, Any]):
        """Show next steps to the user."""
        provider_name = config['name']
        
        self.stdout.write(self.style.SUCCESS("\n🚀 Next Steps:"))
        self.stdout.write("")
        
        # Environment variables
        auth_type = config['auth']['type']
        if auth_type != 'none':
            self.stdout.write("1. Set environment variables:")
            if auth_type == 'bearer_token':
                self.stdout.write(f"   export {provider_name.upper()}_TOKEN='your-token-here'")
            elif auth_type == 'api_key':
                self.stdout.write(f"   export {provider_name.upper()}_API_KEY='your-api-key-here'")
            elif auth_type == 'basic':
                self.stdout.write(f"   export {provider_name.upper()}_USERNAME='your-username'")
                self.stdout.write(f"   export {provider_name.upper()}_PASSWORD='your-password'")
            elif auth_type == 'oauth2':
                self.stdout.write(f"   export {provider_name.upper()}_CLIENT_ID='your-client-id'")
                self.stdout.write(f"   export {provider_name.upper()}_CLIENT_SECRET='your-client-secret'")
            self.stdout.write("")
        
        # Add endpoints
        self.stdout.write("2. Add API endpoints:")
        self.stdout.write(f"   python manage.py add_endpoints --provider {provider_name} --url 'https://api-docs-url'")
        self.stdout.write("")
        
        # Generate type stubs
        self.stdout.write("3. Generate type stubs for IDE support:")
        self.stdout.write(f"   python manage.py generate_type_stubs --provider {provider_name}")
        self.stdout.write("")
        
        # Usage example
        self.stdout.write("4. Use in your code:")
        self.stdout.write(f"   from newfies.smart_api.clients.{provider_name} import {provider_name.title()}APIClient")
        self.stdout.write(f"   client = {provider_name.title()}APIClient()")
        self.stdout.write(f"   response = client.health_check()")
        self.stdout.write("")
    
    def get_provider_path(self, provider_name: str) -> Path:
        """Get the path to provider directory."""
        base_dir = Path(__file__).parent.parent.parent
        return base_dir / "providers" / provider_name
    
    def get_client_path(self, provider_name: str) -> Path:
        """Get the path to client file."""
        base_dir = Path(__file__).parent.parent.parent
        return base_dir / "clients" / f"{provider_name}.py"
    
    # Validation methods
    def validate_provider_name(self, name: str) -> str:
        """Validate provider name."""
        if not re.match(r'^[a-z][a-z0-9_]*$', name):
            raise ValueError("Provider name must start with a letter and contain only lowercase letters, numbers, and underscores")
        return name
    
    def validate_url(self, url: str) -> str:
        """Validate URL format."""
        if not url.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")
        return url.rstrip('/')
    
    def validate_float(self, value: str) -> str:
        """Validate float value."""
        if value:
            try:
                float(value)
            except ValueError:
                raise ValueError("Must be a valid number")
        return value
    
    def validate_int(self, value: str) -> str:
        """Validate integer value."""
        if value:
            try:
                int(value)
            except ValueError:
                raise ValueError("Must be a valid integer")
        return value
    
    # Helper methods for interactive prompts
    def prompt_input(self, prompt: str, default: str = None, required: bool = False, validator=None) -> str:
        """Prompt for user input with validation."""
        while True:
            if default:
                full_prompt = f"{prompt} [{default}]: "
            else:
                full_prompt = f"{prompt}: "
            
            value = input(full_prompt).strip()
            
            if not value and default:
                value = default
            
            if required and not value:
                self.stdout.write(self.style.ERROR("This field is required."))
                continue
            
            if validator and value:
                try:
                    value = validator(value)
                except ValueError as e:
                    self.stdout.write(self.style.ERROR(f"Invalid input: {e}"))
                    continue
            
            return value
    
    def prompt_choice(self, prompt: str, choices: List[str], default: str = None) -> str:
        """Prompt for choice from list."""
        while True:
            if default:
                full_prompt = f"{prompt} {choices} [{default}]: "
            else:
                full_prompt = f"{prompt} {choices}: "
            
            value = input(full_prompt).strip()
            
            if not value and default:
                value = default
            
            if value in choices:
                return value
            
            self.stdout.write(self.style.ERROR(f"Please choose from: {', '.join(choices)}"))
    
    def prompt_yes_no(self, prompt: str, default: bool = None) -> bool:
        """Prompt for yes/no answer."""
        while True:
            if default is True:
                full_prompt = f"{prompt} [Y/n]: "
            elif default is False:
                full_prompt = f"{prompt} [y/N]: "
            else:
                full_prompt = f"{prompt} [y/n]: "
            
            value = input(full_prompt).strip().lower()
            
            if not value and default is not None:
                return default
            
            if value in ['y', 'yes']:
                return True
            elif value in ['n', 'no']:
                return False
            
            self.stdout.write(self.style.ERROR("Please answer 'y' or 'n'")) 