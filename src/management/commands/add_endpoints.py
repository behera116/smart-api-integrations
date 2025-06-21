"""
Django management command to add endpoints to provider configurations using OpenAI.
Reads API documentation from URLs and generates appropriate endpoint configurations.
Uses Jina AI Reader for clean content extraction.

Usage: 
    python manage.py add_endpoints --provider github --url "https://docs.github.com/en/rest/users"
    python manage.py add_endpoints --provider stripe --url "https://stripe.com/docs/api/customers" --dry-run
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class Command(BaseCommand):
    help = 'Add endpoints to provider configurations using OpenAI and Jina AI Reader'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--provider',
            type=str,
            required=True,
            help='Provider name (e.g., github, stripe, hubspot)'
        )
        parser.add_argument(
            '--url',
            type=str,
            required=True,
            help='URL of the API documentation page to parse'
        )
        parser.add_argument(
            '--model',
            type=str,
            default='gpt-4',
            help='OpenAI model to use (default: gpt-4)'
        )
        parser.add_argument(
            '--max-endpoints',
            type=int,
            default=10,
            help='Maximum number of endpoints to extract (default: 10)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be added without modifying files'
        )
        parser.add_argument(
            '--output-format',
            choices=['yaml', 'json'],
            default='yaml',
            help='Output format for generated endpoints (default: yaml)'
        )
    
    def handle(self, *args, **options):
        # Check dependencies
        if not OPENAI_AVAILABLE:
            raise CommandError(
                "OpenAI library not installed. Install with: pip install openai"
            )
        
        if not REQUESTS_AVAILABLE:
            raise CommandError(
                "Requests library not installed. Install with: pip install requests"
            )
        
        # Get OpenAI API key from environment
        openai_key = self.get_openai_key()
        if not openai_key:
            raise CommandError(
                "OpenAI API key required. Set OPENAI_API_KEY environment variable.\n"
                "Example: export OPENAI_API_KEY='your-openai-api-key'"
            )
        
        # Configure OpenAI
        openai.api_key = openai_key
        
        provider_name = options['provider']
        url = options['url']
        
        try:
            # Fetch and parse the documentation page
            self.stdout.write(f"Fetching documentation from: {url}")
            doc_content = self.fetch_documentation(url)
            
            # Get existing provider config
            config_path = self.get_provider_config_path(provider_name)
            existing_config = self.load_existing_config(config_path)
            
            # Generate endpoints using OpenAI
            self.stdout.write("Generating endpoints using OpenAI...")
            new_endpoints = self.generate_endpoints_with_openai(
                doc_content, 
                existing_config, 
                options['model'],
                options['max_endpoints']
            )
            
            if not new_endpoints:
                self.stdout.write(self.style.WARNING("No new endpoints generated."))
                return
            
            # Display results
            self.display_generated_endpoints(new_endpoints, options['output_format'])
            
            if options['dry_run']:
                self.stdout.write(self.style.SUCCESS("Dry run completed. No files were modified."))
                return
            
            # Confirm before adding
            if not self.confirm_addition(new_endpoints):
                self.stdout.write("Operation cancelled.")
                return
            
            # Add endpoints to config
            self.add_endpoints_to_config(config_path, existing_config, new_endpoints)
            
            self.stdout.write(
                self.style.SUCCESS(f"Successfully added {len(new_endpoints)} endpoints to {provider_name}")
            )
            
        except Exception as e:
            raise CommandError(f"Error processing endpoints: {str(e)}")
    
    def get_openai_key(self) -> Optional[str]:
        """Get OpenAI API key from environment variables or Django settings."""
        # Environment variable
        if os.getenv('OPENAI_API_KEY'):
            return os.getenv('OPENAI_API_KEY')
        
        # Django settings
        if hasattr(settings, 'OPENAI_API_KEY'):
            return settings.OPENAI_API_KEY
        
        return None
    
    def fetch_documentation(self, url: str) -> str:
        """Fetch and extract text content from documentation URL using Jina AI Reader."""
        jina_url = f"https://r.jina.ai/{url}"
        
        headers = {
            'User-Agent': 'Smart-API-Endpoint-Generator/1.0'
        }
        
        try:
            self.stdout.write("Using Jina AI Reader for clean content extraction...")
            response = requests.get(jina_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            content = response.text.strip()
            
            # Limit content length
            max_length = 12000  # Jina provides cleaner content, so we can use more
            if len(content) > max_length:
                content = content[:max_length] + "..."
                self.stdout.write(f"Content truncated to {max_length} characters for OpenAI processing")
            
            self.stdout.write(f"✅ Successfully extracted {len(content)} characters of clean content")
            return content
            
        except Exception as e:
            raise CommandError(f"Failed to fetch documentation using Jina AI Reader: {str(e)}")
    
    def get_provider_config_path(self, provider_name: str) -> Path:
        """Get the path to provider's config.yaml file."""
        base_dir = Path(__file__).parent.parent.parent
        config_path = base_dir / "providers" / provider_name / "config.yaml"
        return config_path
    
    def load_existing_config(self, config_path: Path) -> Dict[str, Any]:
        """Load existing provider configuration."""
        if not config_path.exists():
            # Create directory if it doesn't exist
            config_path.parent.mkdir(parents=True, exist_ok=True)
            return {
                'name': config_path.parent.name,
                'base_url': 'https://api.example.com',
                'description': f'{config_path.parent.name.title()} API',
                'auth': {'type': 'bearer_token'},
                'endpoints': {}
            }
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    
    def generate_endpoints_with_openai(
        self, 
        doc_content: str, 
        existing_config: Dict[str, Any],
        model: str,
        max_endpoints: int
    ) -> List[Dict[str, Any]]:
        """Generate endpoint configurations using OpenAI."""
        
        existing_endpoints = list(existing_config.get('endpoints', {}).keys())
        
        prompt = f"""
You are an API documentation parser. Analyze the following API documentation and extract endpoint information.

EXISTING ENDPOINTS (don't duplicate these):
{', '.join(existing_endpoints) if existing_endpoints else 'None'}

PROVIDER INFO:
- Name: {existing_config.get('name', 'Unknown')}
- Base URL: {existing_config.get('base_url', 'Unknown')}
- Description: {existing_config.get('description', 'Unknown')}

DOCUMENTATION CONTENT:
{doc_content}

Extract up to {max_endpoints} API endpoints and return them as a JSON array. For each endpoint, provide:

1. endpoint_name: A descriptive name (snake_case, e.g., "get_user", "create_customer")
2. path: The API path (e.g., "/users/{{id}}", "/customers")
3. method: HTTP method (GET, POST, PUT, DELETE, etc.)
4. description: Brief description of what the endpoint does
5. parameters: Object with parameter definitions (if any)

Parameter format:
{{
  "parameter_name": {{
    "type": "string|integer|boolean|array|object",
    "required": true|false,
    "in": "query|path|header|body",
    "description": "Parameter description"
  }}
}}

Example response:
[
  {{
    "endpoint_name": "get_user",
    "path": "/users/{{id}}",
    "method": "GET",
    "description": "Get user by ID",
    "parameters": {{
      "id": {{
        "type": "string",
        "required": true,
        "in": "path",
        "description": "User ID"
      }}
    }}
  }},
  {{
    "endpoint_name": "create_user",
    "path": "/users",
    "method": "POST",
    "description": "Create a new user",
    "parameters": {{
      "name": {{
        "type": "string",
        "required": true,
        "in": "body",
        "description": "User name"
      }},
      "email": {{
        "type": "string",
        "required": true,
        "in": "body",
        "description": "User email"
      }}
    }}
  }}
]

Only return valid JSON. If no endpoints are found, return an empty array [].
"""
        
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an expert API documentation parser that extracts endpoint information and returns valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.1
            )
            
            content = response.choices[0].message.content.strip()
            
            # Try to extract JSON from the response
            if content.startswith('```json'):
                content = content[7:-3].strip()
            elif content.startswith('```'):
                content = content[3:-3].strip()
            
            endpoints = json.loads(content)
            
            if not isinstance(endpoints, list):
                raise ValueError("Response is not a list")
            
            return endpoints
            
        except json.JSONDecodeError as e:
            raise CommandError(f"Failed to parse OpenAI response as JSON: {str(e)}")
        except Exception as e:
            raise CommandError(f"OpenAI API error: {str(e)}")
    
    def display_generated_endpoints(self, endpoints: List[Dict[str, Any]], output_format: str):
        """Display the generated endpoints."""
        self.stdout.write(self.style.SUCCESS(f"\n=== Generated {len(endpoints)} Endpoints ==="))
        
        for i, endpoint in enumerate(endpoints, 1):
            self.stdout.write(f"\n{i}. {endpoint.get('endpoint_name', 'unnamed')}")
            self.stdout.write(f"   Method: {endpoint.get('method', 'GET')}")
            self.stdout.write(f"   Path: {endpoint.get('path', '/')}")
            self.stdout.write(f"   Description: {endpoint.get('description', 'No description')}")
            
            if endpoint.get('parameters'):
                param_count = len(endpoint['parameters'])
                self.stdout.write(f"   Parameters: {param_count}")
        
        # Show full configuration
        if output_format == 'yaml':
            self.stdout.write(f"\n=== YAML Configuration ===")
            yaml_config = {}
            for endpoint in endpoints:
                endpoint_name = endpoint.pop('endpoint_name')
                yaml_config[endpoint_name] = endpoint
            
            self.stdout.write(yaml.dump(yaml_config, default_flow_style=False, sort_keys=False))
        else:
            self.stdout.write(f"\n=== JSON Configuration ===")
            self.stdout.write(json.dumps(endpoints, indent=2))
    
    def confirm_addition(self, endpoints: List[Dict[str, Any]]) -> bool:
        """Ask user to confirm adding the endpoints."""
        self.stdout.write(f"\nAdd these {len(endpoints)} endpoints to the provider configuration?")
        response = input("Continue? [y/N]: ").strip().lower()
        return response in ['y', 'yes']
    
    def add_endpoints_to_config(
        self, 
        config_path: Path, 
        existing_config: Dict[str, Any], 
        new_endpoints: List[Dict[str, Any]]
    ):
        """Add the new endpoints to the provider configuration."""
        # Ensure endpoints section exists
        if 'endpoints' not in existing_config:
            existing_config['endpoints'] = {}
        
        # Add new endpoints
        for endpoint in new_endpoints:
            endpoint_name = endpoint.pop('endpoint_name')
            existing_config['endpoints'][endpoint_name] = endpoint
        
        # Write back to file
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(existing_config, f, default_flow_style=False, sort_keys=False)
        
        self.stdout.write(f"✅ Updated configuration: {config_path}") 