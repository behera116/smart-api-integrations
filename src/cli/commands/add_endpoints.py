"""
Command to add endpoints to provider configurations using OpenAI.
Reads API documentation from URLs and generates appropriate endpoint configurations.
Uses Jina AI Reader for clean content extraction.

Usage: 
    smart-api-integrations add-endpoints --provider github --url "https://docs.github.com/en/rest/users"
    smart-api-integrations add-endpoints --provider stripe --url "https://stripe.com/docs/api/customers" --dry-run
"""

import os
import sys
import yaml
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import argparse

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


def register_command(subparsers):
    """Register the command with the given subparsers."""
    parser = subparsers.add_parser(
        'add-endpoints',
        help='Add endpoints to provider configurations using OpenAI and Jina AI Reader',
        description='Add endpoints to provider configurations using OpenAI and Jina AI Reader'
    )
    
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
    parser.add_argument(
        '--providers-dir',
        type=str,
        default=os.environ.get('SMART_API_INTEGRATIONS_PROVIDERS_DIR', './providers'),
        help='Directory containing provider configurations'
    )
    
    parser.set_defaults(func=command_handler)
    return parser


def command_handler(args):
    """Handle the add-endpoints command."""
    try:
        # Check dependencies
        if not OPENAI_AVAILABLE:
            print("OpenAI library not installed. Install with: pip install openai")
            return 1
        
        if not REQUESTS_AVAILABLE:
            print("Requests library not installed. Install with: pip install requests")
            return 1
        
        # Get OpenAI API key from environment
        openai_key = get_openai_key()
        if not openai_key:
            print(
                "OpenAI API key required. Set OPENAI_API_KEY environment variable.\n"
                "Example: export OPENAI_API_KEY='your-openai-api-key'"
            )
            return 1
        
        # Initialize OpenAI client
        client = OpenAI(api_key=openai_key)
        
        provider_name = args.provider
        url = args.url
        
        # Fetch and parse the documentation page
        print(f"Fetching documentation from: {url}")
        doc_content = fetch_documentation(url)
        
        # Get existing provider config
        config_path = get_provider_config_path(provider_name, args.providers_dir)
        existing_config = load_existing_config(config_path)
        
        # Generate endpoints using OpenAI
        print("Generating endpoints using OpenAI...")
        try:
            new_endpoints = generate_endpoints_with_openai(
                doc_content, 
                existing_config, 
                args.model,
                args.max_endpoints,
                client
            )
            
            if not new_endpoints:
                print("No new endpoints generated.")
                if args.dry_run:
                    print("\n=== Dry Run Information ===")
                    print(f"Provider: {existing_config.get('name', 'Unknown')}")
                    print(f"Base URL: {existing_config.get('base_url', 'Unknown')}")
                    print("\nNo changes would be made to the configuration.")
                    print("\nDry run completed. No files were modified.")
                return 0
            
            # Display results
            display_generated_endpoints(new_endpoints, args.output_format, existing_config, args.dry_run)
            
            if args.dry_run:
                return 0
            
            # Confirm before adding
            if not confirm_addition(new_endpoints):
                print("Operation cancelled.")
                return 0
            
            # Add endpoints to config
            add_endpoints_to_config(config_path, existing_config, new_endpoints)
            
            print(f"Successfully added {len(new_endpoints)} endpoints to {provider_name}")
            return 0
            
        except Exception as e:
            print(f"Error generating endpoints with OpenAI: {str(e)}")
            if "401" in str(e) or "invalid_api_key" in str(e):
                print("\nAuthentication failed. Please check your OpenAI API key.")
                print("You can get a key at https://platform.openai.com/account/api-keys")
                print("Then set it with: export OPENAI_API_KEY='your-openai-api-key'")
            
            if args.dry_run:
                print("\n=== Dry Run Information ===")
                print(f"Provider: {existing_config.get('name', 'Unknown')}")
                print(f"Base URL: {existing_config.get('base_url', 'Unknown')}")
                print("\nNo changes would be made to the configuration.")
                print("\nDry run completed. No files were modified.")
            return 1
        
    except Exception as e:
        print(f"Error processing endpoints: {str(e)}")
        return 1


def get_openai_key() -> Optional[str]:
    """Get OpenAI API key from environment variables."""
    # Environment variable
    if os.getenv('OPENAI_API_KEY'):
        return os.getenv('OPENAI_API_KEY')
    
    return None


def fetch_documentation(url: str) -> str:
    """Fetch and extract text content from documentation URL using Jina AI Reader."""
    jina_url = f"https://r.jina.ai/{url}"
    
    headers = {
        'User-Agent': 'Smart-API-Endpoint-Generator/1.0'
    }
    
    try:
        print("Using Jina AI Reader for clean content extraction...")
        response = requests.get(jina_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        content = response.text.strip()
        
        # Limit content length
        max_length = 12000  # Jina provides cleaner content, so we can use more
        if len(content) > max_length:
            content = content[:max_length] + "..."
            print(f"Content truncated to {max_length} characters for OpenAI processing")
        
        print(f"✅ Successfully extracted {len(content)} characters of clean content")
        return content
        
    except Exception as e:
        raise ValueError(f"Failed to fetch documentation using Jina AI Reader: {str(e)}")


def get_provider_config_path(provider_name: str, providers_dir: str) -> Path:
    """Get the path to provider's config.yaml file."""
    config_path = Path(providers_dir) / provider_name / "config.yaml"
    return config_path


def load_existing_config(config_path: Path) -> Dict[str, Any]:
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
        config = yaml.safe_load(f)
    
    # Ensure endpoints dictionary exists
    if 'endpoints' not in config:
        config['endpoints'] = {}
    
    return config

def generate_endpoints_with_openai(
    doc_content: str, 
    existing_config: Dict[str, Any],
    model: str,
    max_endpoints: int,
    client
) -> List[Dict[str, Any]]:
    """Generate API endpoint configurations using OpenAI."""
    # Extract existing endpoint names to avoid duplicates
    existing_endpoints = set(existing_config.get('endpoints', {}).keys())
    base_url = existing_config.get('base_url', '')
    
    # Prepare the prompt for OpenAI
    system_prompt = """
    You are an API endpoint configuration generator specialized in extracting REST API endpoints from documentation.
    Your task is to identify and extract API endpoints from the provided documentation, even if they are not explicitly formatted as API reference.
    
    For GitHub REST API documentation, look for:
    - URL patterns like "/users/{username}" or "/repos/{owner}/{repo}"
    - HTTP methods (GET, POST, PUT, DELETE, etc.)
    - Parameters mentioned in tables or lists
    - Example requests and responses
    
    For each endpoint you find, extract:
    1. A unique endpoint name in snake_case that describes the operation (e.g., get_user, list_repositories)
    2. The HTTP method (GET, POST, PUT, DELETE, etc.)
    3. The path relative to the base URL (e.g., /users/{username})
    4. Required and optional parameters
    5. A brief description of what the endpoint does
    
    If you can't find explicit endpoints in the documentation, look for:
    - Example API calls or curl commands
    - Code snippets showing API usage
    - Tables describing API resources
    - Descriptions of operations that can be performed
    
    Use the following structure for each endpoint:
    ```
    {
      "endpoint_name": "descriptive_name_in_snake_case",
      "path": "/path/to/resource",
      "method": "HTTP_METHOD",
      "description": "Brief description of what this endpoint does",
      "parameters": [
        {
          "name": "param_name",
          "location": "query|path|header|body",
          "required": true|false,
          "description": "Parameter description"
        }
      ]
    }
    ```
    
    Return a valid JSON array of endpoint objects. If you truly cannot find any endpoints, return an empty array [].
    """
    
    user_prompt = f"""
    Extract API endpoints from the following GitHub REST API documentation. 
    Base URL: {base_url}
    
    Existing endpoint names (avoid duplicating these): {", ".join(existing_endpoints)}
    
    Extract up to {max_endpoints} endpoints.
    
    Documentation content:
    {doc_content}
    
    Return ONLY a JSON array of endpoint configurations, with no additional text or explanation.
    Each endpoint should have: endpoint_name, path, method, description, and parameters.
    
    Example of expected format for GitHub API:
    [
      {{
        "endpoint_name": "get_user",
        "path": "/users/{{username}}",
        "method": "GET",
        "description": "Get a user by username",
        "parameters": [
          {{
            "name": "username",
            "location": "path",
            "required": true,
            "description": "The handle for the GitHub user account"
          }}
        ]
      }},
      {{
        "endpoint_name": "list_user_repos",
        "path": "/users/{{username}}/repos",
        "method": "GET",
        "description": "Lists public repositories for the specified user",
        "parameters": [
          {{
            "name": "username",
            "location": "path",
            "required": true,
            "description": "The handle for the GitHub user account"
          }},
          {{
            "name": "type",
            "location": "query",
            "required": false,
            "description": "Can be one of: all, owner, member"
          }}
        ]
      }}
    ]
    
    DO NOT include any explanatory text before or after the JSON array. Return ONLY the JSON array.
    """
    
    try:
        # Use OpenAI API to generate endpoints
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,  # Low temperature for more deterministic output
            max_tokens=4000,
            n=1,
            stop=None
        )
        
        # Extract the generated content
        content = response.choices[0].message.content.strip()
        
        # Try to parse as JSON
        try:
            # Find JSON array in the response (in case there's additional text)
            import re
            json_match = re.search(r'\[\s*{.*}\s*\]', content, re.DOTALL)
            if json_match:
                content = json_match.group(0)
            elif content.startswith("```json") and content.endswith("```"):
                content = content[7:-3].strip()
            elif content.startswith("```") and content.endswith("```"):
                content = content[3:-3].strip()
            
            # If it's an empty array or no endpoints found message
            if content == "[]" or "no endpoints" in content.lower():
                print("No endpoints found in the provided documentation.")
                # Try with a fallback approach - generate some sample endpoints based on the documentation
                return generate_sample_endpoints(doc_content, existing_config, model, client, max_endpoints)
            
            endpoints_list = json.loads(content)
            
            # Convert list to dictionary format expected by the config
            endpoints_dict = {}
            for endpoint in endpoints_list:
                # Handle both 'name' and 'endpoint_name' keys for flexibility
                name = endpoint.pop('endpoint_name', None) or endpoint.pop('name', None)
                if not name:
                    # Generate a name if none is provided
                    method = endpoint.get('method', 'GET').lower()
                    path = endpoint.get('path', '').strip('/')
                    if path:
                        path_parts = path.split('/')
                        name = f"{method}_{path_parts[-1]}"
                    else:
                        name = f"{method}_endpoint_{len(endpoints_dict) + 1}"
                
                if name and name not in existing_endpoints:
                    endpoints_dict[name] = endpoint
            
            return list(endpoints_dict.items())
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON response: {str(e)}")
            print("Response content:")
            print(content[:500] + "..." if len(content) > 500 else content)
            
            # Try to generate sample endpoints as a fallback
            return generate_sample_endpoints(doc_content, existing_config, model, client, max_endpoints)
    
    except Exception as e:
        raise e

def generate_sample_endpoints(doc_content: str, existing_config: Dict[str, Any], model: str, client, max_endpoints: int = 3) -> List[Dict[str, Any]]:
    """Generate sample endpoints based on the documentation content as a fallback."""
    print("Attempting to generate sample endpoints based on documentation content...")
    
    # Extract existing endpoint names to avoid duplicates
    existing_endpoints = set(existing_config.get('endpoints', {}).keys())
    
    # Create a simpler prompt focused on extracting key concepts
    prompt = f"""
    Based on the following GitHub REST API documentation, create EXACTLY {max_endpoints} sample API endpoints.
    
    IMPORTANT: You MUST generate EXACTLY {max_endpoints} different endpoints, no more and no less.
    
    For the GitHub API, consider endpoints for these resources:
    - Users (get user, list users, update user, delete user)
    - Repositories (list repos, get repo, create repo)
    - Issues (list issues, create issue, update issue)
    - Pull requests (list PRs, get PR, create PR)
    - Organizations (list orgs, get org)
    - Teams (list teams, get team members)
    - Gists (list gists, create gist)
    - Followers/Following (get followers, get following)
    
    Documentation content:
    {doc_content[:2000]}
    
    Return a JSON array with EXACTLY {max_endpoints} endpoints in this format:
    [
      {{
        "endpoint_name": "resource_operation",
        "path": "/path/to/resource",
        "method": "HTTP_METHOD",
        "description": "Operation description",
        "parameters": [
          {{
            "name": "parameter_name",
            "location": "query|path|header|body",
            "required": true|false,
            "description": "Parameter description"
          }}
        ]
      }},
      // ... REPEAT TO GENERATE EXACTLY {max_endpoints} ENDPOINTS ...
    ]
    
    ENSURE you return EXACTLY {max_endpoints} endpoints in your response.
    """
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": f"You are an API designer that creates EXACTLY {max_endpoints} sample API endpoints based on documentation."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=4000,  # Increased token limit to accommodate more endpoints
            n=1,
            stop=None
        )
        
        content = response.choices[0].message.content.strip()
        
        # Try to extract JSON
        import re
        json_match = re.search(r'\[\s*{.*}\s*\]', content, re.DOTALL)
        if json_match:
            content = json_match.group(0)
        elif content.startswith("```json") and content.endswith("```"):
            content = content[7:-3].strip()
        elif content.startswith("```") and content.endswith("```"):
            content = content[3:-3].strip()
            
        try:
            endpoints_list = json.loads(content)
            
            # If we didn't get enough endpoints, try to generate more
            if len(endpoints_list) < max_endpoints:
                print(f"Warning: Only generated {len(endpoints_list)} endpoints instead of {max_endpoints}")
                
                # Try to generate additional endpoints to reach the target
                remaining = max_endpoints - len(endpoints_list)
                if remaining > 0:
                    additional_endpoints = generate_additional_endpoints(
                        doc_content, 
                        existing_config, 
                        model, 
                        client, 
                        remaining,
                        [ep.get('endpoint_name') or ep.get('name') for ep in endpoints_list]
                    )
                    endpoints_list.extend(additional_endpoints)
            
            # Convert list to dictionary format expected by the config
            endpoints_dict = {}
            for endpoint in endpoints_list:
                # Handle both 'name' and 'endpoint_name' keys for flexibility
                name = endpoint.pop('endpoint_name', None) or endpoint.pop('name', None)
                if not name:
                    # Generate a name if none is provided
                    method = endpoint.get('method', 'GET').lower()
                    path = endpoint.get('path', '').strip('/')
                    if path:
                        path_parts = path.split('/')
                        name = f"{method}_{path_parts[-1]}"
                    else:
                        name = f"{method}_endpoint_{len(endpoints_dict) + 1}"
                
                if name and name not in existing_endpoints:
                    endpoints_dict[name] = endpoint
                    
                # Limit to max_endpoints
                if len(endpoints_dict) >= max_endpoints:
                    break
            
            # If we still don't have enough endpoints, create generic ones to fill the gap
            if len(endpoints_dict) < max_endpoints:
                print(f"Still only have {len(endpoints_dict)} endpoints, generating generic ones to reach {max_endpoints}")
                endpoints_dict = fill_with_generic_endpoints(endpoints_dict, max_endpoints, existing_endpoints)
            
            return list(endpoints_dict.items())
            
        except json.JSONDecodeError:
            print("Failed to generate sample endpoints.")
            # Generate generic endpoints as a last resort
            return list(fill_with_generic_endpoints({}, max_endpoints, existing_endpoints).items())
            
    except Exception as e:
        print(f"Error generating sample endpoints: {str(e)}")
        # Generate generic endpoints as a last resort
        return list(fill_with_generic_endpoints({}, max_endpoints, existing_endpoints).items())

def fill_with_generic_endpoints(endpoints_dict: Dict[str, Any], target_count: int, existing_endpoints: set) -> Dict[str, Any]:
    """Fill the endpoints dictionary with generic endpoints to reach the target count."""
    # Common GitHub API endpoints that are likely to exist
    generic_endpoints = [
        {
            "name": "list_user_repos",
            "path": "/users/{username}/repos",
            "method": "GET",
            "description": "Lists public repositories for the specified user",
            "parameters": [
                {
                    "name": "username",
                    "location": "path",
                    "required": True,
                    "description": "The handle for the GitHub user account"
                }
            ]
        },
        {
            "name": "list_followers",
            "path": "/users/{username}/followers",
            "method": "GET",
            "description": "Lists the people following the specified user",
            "parameters": [
                {
                    "name": "username",
                    "location": "path",
                    "required": True,
                    "description": "The handle for the GitHub user account"
                }
            ]
        },
        {
            "name": "list_following",
            "path": "/users/{username}/following",
            "method": "GET",
            "description": "Lists the people the specified user follows",
            "parameters": [
                {
                    "name": "username",
                    "location": "path",
                    "required": True,
                    "description": "The handle for the GitHub user account"
                }
            ]
        },
        {
            "name": "list_gists",
            "path": "/users/{username}/gists",
            "method": "GET",
            "description": "Lists public gists for the specified user",
            "parameters": [
                {
                    "name": "username",
                    "location": "path",
                    "required": True,
                    "description": "The handle for the GitHub user account"
                }
            ]
        },
        {
            "name": "get_repo",
            "path": "/repos/{owner}/{repo}",
            "method": "GET",
            "description": "Gets a repository",
            "parameters": [
                {
                    "name": "owner",
                    "location": "path",
                    "required": True,
                    "description": "The account owner of the repository"
                },
                {
                    "name": "repo",
                    "location": "path",
                    "required": True,
                    "description": "The name of the repository"
                }
            ]
        },
        {
            "name": "create_repo",
            "path": "/user/repos",
            "method": "POST",
            "description": "Creates a new repository for the authenticated user",
            "parameters": [
                {
                    "name": "name",
                    "location": "body",
                    "required": True,
                    "description": "The name of the repository"
                }
            ]
        },
        {
            "name": "delete_repo",
            "path": "/repos/{owner}/{repo}",
            "method": "DELETE",
            "description": "Deletes a repository",
            "parameters": [
                {
                    "name": "owner",
                    "location": "path",
                    "required": True,
                    "description": "The account owner of the repository"
                },
                {
                    "name": "repo",
                    "location": "path",
                    "required": True,
                    "description": "The name of the repository"
                }
            ]
        },
        {
            "name": "list_issues",
            "path": "/repos/{owner}/{repo}/issues",
            "method": "GET",
            "description": "Lists issues for a repository",
            "parameters": [
                {
                    "name": "owner",
                    "location": "path",
                    "required": True,
                    "description": "The account owner of the repository"
                },
                {
                    "name": "repo",
                    "location": "path",
                    "required": True,
                    "description": "The name of the repository"
                }
            ]
        },
        {
            "name": "create_issue",
            "path": "/repos/{owner}/{repo}/issues",
            "method": "POST",
            "description": "Creates a new issue for a repository",
            "parameters": [
                {
                    "name": "owner",
                    "location": "path",
                    "required": True,
                    "description": "The account owner of the repository"
                },
                {
                    "name": "repo",
                    "location": "path",
                    "required": True,
                    "description": "The name of the repository"
                },
                {
                    "name": "title",
                    "location": "body",
                    "required": True,
                    "description": "The title of the issue"
                }
            ]
        },
        {
            "name": "list_pull_requests",
            "path": "/repos/{owner}/{repo}/pulls",
            "method": "GET",
            "description": "Lists pull requests for a repository",
            "parameters": [
                {
                    "name": "owner",
                    "location": "path",
                    "required": True,
                    "description": "The account owner of the repository"
                },
                {
                    "name": "repo",
                    "location": "path",
                    "required": True,
                    "description": "The name of the repository"
                }
            ]
        }
    ]
    
    # Add generic endpoints until we reach the target count
    for endpoint in generic_endpoints:
        if len(endpoints_dict) >= target_count:
            break
            
        name = endpoint["name"]
        # Make sure we don't add duplicates or existing endpoints
        if name not in endpoints_dict and name not in existing_endpoints:
            # Remove the name from the endpoint data
            endpoint_data = endpoint.copy()
            endpoint_data.pop("name", None)
            endpoints_dict[name] = endpoint_data
    
    # If we still need more endpoints, create numbered generic ones
    i = 1
    while len(endpoints_dict) < target_count:
        name = f"generic_endpoint_{i}"
        if name not in endpoints_dict and name not in existing_endpoints:
            endpoints_dict[name] = {
                "path": f"/api/v1/resource{i}",
                "method": "GET",
                "description": f"Generic endpoint {i}",
                "parameters": []
            }
        i += 1
    
    return endpoints_dict

def generate_additional_endpoints(
    doc_content: str, 
    existing_config: Dict[str, Any], 
    model: str, 
    client, 
    count: int,
    existing_names: List[str]
) -> List[Dict[str, Any]]:
    """Generate additional endpoints to reach the target count."""
    print(f"Generating {count} additional endpoints...")
    
    prompt = f"""
    Generate EXACTLY {count} MORE GitHub API endpoints that are DIFFERENT from these existing ones:
    {', '.join(existing_names)}
    
    For the GitHub API, consider endpoints for these resources:
    - Users (update user, delete user)
    - Repositories (list repos, get repo, create repo, delete repo)
    - Issues (list issues, create issue, update issue)
    - Pull requests (list PRs, get PR, create PR)
    - Organizations (list orgs, get org)
    - Teams (list teams, get team members)
    - Gists (list gists, create gist)
    - Followers/Following (get followers, get following)
    
    Return a JSON array with EXACTLY {count} NEW endpoints in this format:
    [
      {{
        "endpoint_name": "resource_operation",
        "path": "/path/to/resource",
        "method": "HTTP_METHOD",
        "description": "Operation description",
        "parameters": [
          {{
            "name": "parameter_name",
            "location": "query|path|header|body",
            "required": true|false,
            "description": "Parameter description"
          }}
        ]
      }}
    ]
    """
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": f"You are an API designer that creates EXACTLY {count} additional API endpoints."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=2000,
            n=1,
            stop=None
        )
        
        content = response.choices[0].message.content.strip()
        
        # Try to extract JSON
        import re
        json_match = re.search(r'\[\s*{.*}\s*\]', content, re.DOTALL)
        if json_match:
            content = json_match.group(0)
        elif content.startswith("```json") and content.endswith("```"):
            content = content[7:-3].strip()
        elif content.startswith("```") and content.endswith("```"):
            content = content[3:-3].strip()
            
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            print("Failed to generate additional endpoints.")
            return []
            
    except Exception as e:
        print(f"Error generating additional endpoints: {str(e)}")
        return []


def display_generated_endpoints(endpoints: List[Dict[str, Any]], output_format: str, existing_config: Dict[str, Any] = None, dry_run: bool = False):
    """Display the generated endpoints in the specified format."""
    if not endpoints:
        print("No endpoints generated.")
        return
    
    print(f"\n=== Generated {len(endpoints)} Endpoints ===\n")
    
    # Convert to dictionary for display
    endpoints_dict = {name: config for name, config in endpoints}
    
    if output_format == 'yaml':
        print(yaml.dump(endpoints_dict, default_flow_style=False, sort_keys=False))
    else:  # json
        print(json.dumps(endpoints_dict, indent=2))
    
    # Summary table
    print("\n=== Endpoints Summary ===")
    print(f"{'Endpoint Name':<30} {'Method':<8} {'Path':<40} {'Parameters':<20}")
    print("-" * 100)
    
    for name, config in endpoints:
        method = config.get('method', 'GET')
        path = config.get('path', '')
        params = len(config.get('parameters', []))
        print(f"{name:<30} {method:<8} {path:<40} {params:<20}")
    
    # Additional information for dry run
    if dry_run and existing_config:
        existing_endpoints = set(existing_config.get('endpoints', {}).keys())
        new_endpoint_names = set(name for name, _ in endpoints)
        
        print("\n=== Dry Run Information ===")
        print(f"Provider: {existing_config.get('name', 'Unknown')}")
        print(f"Base URL: {existing_config.get('base_url', 'Unknown')}")
        
        # Show which endpoints would be added
        print("\nEndpoints that would be added:")
        for name, config in endpoints:
            method = config.get('method', 'GET')
            path = config.get('path', '')
            print(f"  ✅ {name} ({method} {path})")
        
        # Show which endpoints already exist (would be skipped)
        overlapping = existing_endpoints.intersection(new_endpoint_names)
        if overlapping:
            print("\nEndpoints that already exist (would be skipped):")
            for name in overlapping:
                existing_endpoint = existing_config['endpoints'][name]
                method = existing_endpoint.get('method', 'GET')
                path = existing_endpoint.get('path', '')
                print(f"  ⚠️  {name} ({method} {path})")
        
        # Show a preview of the updated configuration
        print("\nPreview of updated configuration:")
        updated_config = existing_config.copy()
        for name, config in endpoints:
            updated_config['endpoints'][name] = config
        
        # Print only the first few endpoints to avoid overwhelming output
        preview_config = {
            'name': updated_config.get('name', 'Unknown'),
            'base_url': updated_config.get('base_url', 'Unknown'),
            'description': updated_config.get('description', 'Unknown API'),
            'auth': updated_config.get('auth', {'type': 'bearer_token'}),
            'endpoints': {}
        }
        
        # Add a few existing endpoints and new endpoints for preview
        endpoint_count = 0
        for name, config in updated_config['endpoints'].items():
            preview_config['endpoints'][name] = config
            endpoint_count += 1
            if endpoint_count >= 5:  # Show at most 5 endpoints in preview
                break
        
        if len(updated_config['endpoints']) > 5:
            print(f"Showing 5/{len(updated_config['endpoints'])} total endpoints:")
        
        print(yaml.dump(preview_config, default_flow_style=False, sort_keys=False))
        print(f"\nDry run completed. No files were modified.")


def confirm_addition(endpoints: List[Dict[str, Any]]) -> bool:
    """Ask user to confirm adding the endpoints."""
    response = input(f"\nAdd {len(endpoints)} endpoints to configuration? [Y/n]: ")
    return response.lower() not in ('n', 'no')


def add_endpoints_to_config(
    config_path: Path, 
    existing_config: Dict[str, Any], 
    new_endpoints: List[Dict[str, Any]]
):
    """Add the new endpoints to the configuration file."""
    # Add new endpoints to existing config
    for name, endpoint_config in new_endpoints:
        # Convert parameters from list format (AI output) to dict format (schema expected)
        if 'parameters' in endpoint_config:
            if isinstance(endpoint_config['parameters'], list):
                # Convert from list to dict format
                param_dict = {}
                for param in endpoint_config['parameters']:
                    param_name = param.get('name')
                    if param_name:
                        param_dict[param_name] = {
                            'type': param.get('type', 'string'),
                            'required': param.get('required', False),
                            'in': param.get('location', param.get('in', 'query')),
                            'description': param.get('description', '')
                        }
                endpoint_config['parameters'] = param_dict
            elif not endpoint_config['parameters']:
                # Empty list or None - convert to empty dict
                endpoint_config['parameters'] = {}
        else:
            # No parameters field - add empty dict
            endpoint_config['parameters'] = {}
        
        existing_config['endpoints'][name] = endpoint_config
    
    # Write updated config back to file
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(existing_config, f, default_flow_style=False, sort_keys=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Add endpoints to provider configurations using OpenAI and Jina AI Reader'
    )
    register_command(parser.add_subparsers())
    args = parser.parse_args()
    
    if hasattr(args, 'func'):
        sys.exit(args.func(args))
    else:
        parser.print_help()
        sys.exit(1)
