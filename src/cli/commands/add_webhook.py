"""
Command to add webhook endpoints to a provider configuration.

This command allows you to add webhook configurations to existing providers.

Usage:
    smart-api-integrations add-webhook github --event push --secret-env GITHUB_WEBHOOK_SECRET
    smart-api-integrations add-webhook stripe --event payment_intent.succeeded --secret-env STRIPE_WEBHOOK_SECRET
"""

import os
import sys
import argparse
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List

try:
    # When installed as package
    from smart_api_integrations.core.webhook_schema import WebhookVerificationType
except ImportError:
    # For local development
    import sys
    from pathlib import Path
    
    # Add parent directory to path if running as script
    if __name__ == "__main__":
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    
    from src.core.webhook_schema import WebhookVerificationType


def register_command(subparsers):
    """Register the command with the given subparsers."""
    parser = subparsers.add_parser(
        'add-webhook',
        help='Add webhook configuration to a provider',
        description='Add webhook configuration to a provider'
    )
    
    parser.add_argument(
        'provider',
        type=str,
        help='Provider name (e.g., stripe, github)'
    )
    
    parser.add_argument(
        '--name',
        type=str,
        default='default',
        help='Webhook name (default: default)'
    )
    
    parser.add_argument(
        '--path',
        type=str,
        help='Webhook path (default: /webhooks/{provider}/)'
    )
    
    parser.add_argument(
        '--event',
        type=str,
        action='append',
        help='Event types to handle (can be specified multiple times)'
    )
    
    parser.add_argument(
        '--secret-env',
        type=str,
        help='Environment variable name for the webhook secret'
    )
    
    parser.add_argument(
        '--verification-type',
        type=str,
        choices=['hmac_sha256', 'hmac_sha1', 'rsa', 'none'],
        default='hmac_sha256',
        help='Signature verification type (default: hmac_sha256)'
    )
    
    parser.add_argument(
        '--signature-header',
        type=str,
        help='HTTP header containing the signature'
    )
    
    parser.add_argument(
        '--timestamp-header',
        type=str,
        help='HTTP header containing the timestamp (if required)'
    )
    
    parser.add_argument(
        '--providers-dir',
        help='Directory containing provider configurations',
        default=os.environ.get('SMART_API_INTEGRATIONS_PROVIDERS_DIR', './providers')
    )
    
    parser.set_defaults(func=command_handler)
    return parser


def command_handler(args):
    """Handle the add-webhook command."""
    try:
        provider_name = args.provider
        webhook_name = args.name
        providers_dir = Path(args.providers_dir)
        
        # Check if provider exists
        provider_dir = providers_dir / provider_name
        if not provider_dir.exists():
            print(f"❌ Provider not found: {provider_name}")
            print(f"Create the provider first using the add-provider command.")
            return 1
        
        # Check if provider config exists
        config_path = provider_dir / "config.yaml"
        if not config_path.exists():
            print(f"❌ Provider configuration not found: {config_path}")
            return 1
        
        # Load provider configuration
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Create webhook config path
        webhook_config_path = provider_dir / "webhook.yaml"
        
        # Load existing webhook config if it exists
        if webhook_config_path.exists():
            with open(webhook_config_path, 'r') as f:
                webhook_config = yaml.safe_load(f)
        else:
            webhook_config = {
                'webhooks': {}
            }
        
        # Ensure webhooks section exists
        if 'webhooks' not in webhook_config:
            webhook_config['webhooks'] = {}
        
        # Create or update webhook configuration
        if webhook_name in webhook_config['webhooks']:
            print(f"⚠️ Updating existing webhook: {webhook_name}")
            webhook = webhook_config['webhooks'][webhook_name]
        else:
            print(f"✅ Creating new webhook: {webhook_name}")
            webhook = {}
            webhook_config['webhooks'][webhook_name] = webhook
        
        # Set webhook path
        if args.path:
            webhook['path'] = args.path
        elif 'path' not in webhook:
            webhook['path'] = f"/webhooks/{provider_name}/{webhook_name if webhook_name != 'default' else ''}"
            # Clean up double slashes
            webhook['path'] = webhook['path'].replace('//', '/')
        
        # Set verification settings
        if args.verification_type:
            webhook['verification_type'] = args.verification_type
        
        if args.secret_env:
            webhook['signing_secret_env'] = args.secret_env
            webhook['verify_signature'] = True
        
        if args.signature_header:
            webhook['signature_header'] = args.signature_header
        
        if args.timestamp_header:
            webhook['timestamp_header'] = args.timestamp_header
        
        # Add events
        if args.event:
            if 'events' not in webhook:
                webhook['events'] = []
            
            for event in args.event:
                if event not in webhook['events']:
                    webhook['events'].append(event)
        
        # Save webhook configuration
        with open(webhook_config_path, 'w') as f:
            yaml.dump(webhook_config, f, default_flow_style=False)
        
        print(f"✅ Webhook configuration saved: {webhook_config_path}")
        
        # Generate example handler
        example_handler = generate_example_handler(provider_name, webhook_name, args.event or [])
        print("\n📝 Example webhook handler:")
        print(example_handler)
        
        # Generate example URL
        example_url = f"/webhooks/{provider_name}/{webhook_name if webhook_name != 'default' else ''}"
        example_url = example_url.replace('//', '/')
        
        print("\n🔗 Webhook URL:")
        print(f"POST {example_url}")
        
        # Show framework integration examples
        print("\n🔌 Framework Integration:")
        print_framework_examples(provider_name, webhook_name)
        
        return 0
        
    except Exception as e:
        print(f"❌ Error adding webhook: {str(e)}")
        return 1


def generate_example_handler(provider: str, webhook_name: str, events: List[str]):
    """Generate example webhook handler code."""
    if not events:
        events = ["example_event"]
    
    example = f"""
from smart_api_integrations.webhooks.decorators import webhook_handler

@webhook_handler('{provider}', '{events[0]}'{',' if webhook_name != 'default' else ''} '{webhook_name}')
def handle_{provider}_{events[0].replace('.', '_')}(event):
    \"\"\"Handle {provider} {events[0]} event.\"\"\"
    # Access event data
    payload = event.payload
    
    # Your business logic here
    
    # Return response
    return {{
        'success': True,
        'message': 'Event processed successfully',
        'data': {{
            'event_id': event.id,
            'event_type': event.type
        }}
    }}
"""
    
    if len(events) > 1:
        example += f"""
# Handle multiple events
@webhook_handler('{provider}', '{events[1]}'{',' if webhook_name != 'default' else ''} '{webhook_name}')
def handle_{provider}_{events[1].replace('.', '_')}(event):
    \"\"\"Handle {provider} {events[1]} event.\"\"\"
    # Your business logic here
    return {{'success': True}}
"""
    
    return example


def print_framework_examples(provider: str, webhook_name: str):
    """Print examples for integrating with different frameworks."""
    url = f"/webhooks/{provider}/{webhook_name if webhook_name != 'default' else ''}"
    url = url.replace('//', '/')
    
    # Flask example
    print("Flask:")
    print(f"""```python
from flask import Flask
from smart_api_integrations.frameworks.flask import init_flask_app

app = Flask(__name__)
init_flask_app(app)

# Webhook URL will be: {url}
```""")
    
    # FastAPI example
    print("\nFastAPI:")
    print(f"""```python
from fastapi import FastAPI
from smart_api_integrations.frameworks.fastapi import init_fastapi_app

app = FastAPI()
init_fastapi_app(app)

# Webhook URL will be: {url}
```""")
    
    # Django example
    print("\nDjango:")
    print(f"""```python
# In urls.py
from django.urls import path, include
from smart_api_integrations.frameworks.django import get_webhook_urls

urlpatterns = [
    # ... your other URL patterns
    path('api/', include(get_webhook_urls())),
]

# Webhook URL will be: /api{url}
```""")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Add webhook configuration to a provider'
    )
    register_command(parser.add_subparsers())
    args = parser.parse_args()
    
    if hasattr(args, 'func'):
        sys.exit(args.func(args))
    else:
        parser.print_help()
        sys.exit(1) 