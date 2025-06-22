"""
Command to generate webhook handler classes.

This command generates a webhook handler class for a specific provider.
"""

import os
import sys
import argparse
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional

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
        'generate-webhook-handler',
        help='Generate a webhook handler class for a provider',
        description='Generate a webhook handler class for a provider'
    )
    
    parser.add_argument(
        'provider',
        type=str,
        help='Provider name (e.g., stripe, github)'
    )
    
    parser.add_argument(
        '--events',
        type=str,
        nargs='+',
        help='Event types to handle (e.g., push pull_request)'
    )
    
    parser.add_argument(
        '--class-name',
        type=str,
        help='Class name for the handler (default: {Provider}WebhookHandler)'
    )
    
    parser.add_argument(
        '--output-file',
        type=str,
        help='Output file path (default: ./{provider}_webhook_handler.py)'
    )
    
    parser.add_argument(
        '--providers-dir',
        help='Directory containing provider configurations',
        default=os.environ.get('SMART_API_INTEGRATIONS_PROVIDERS_DIR', './providers')
    )
    
    parser.set_defaults(func=command_handler)
    return parser


def command_handler(args):
    """Handle the generate-webhook-handler command."""
    try:
        provider_name = args.provider
        providers_dir = Path(args.providers_dir)
        
        # Check if provider exists
        provider_dir = providers_dir / provider_name
        if not provider_dir.exists():
            print(f"❌ Provider not found: {provider_name}")
            print(f"Create the provider first using the add-provider command.")
            return 1
        
        # Get events from webhook config if not provided
        events = args.events
        if not events:
            # Check if webhook config exists
            webhook_config_path = provider_dir / "webhook.yaml"
            if webhook_config_path.exists():
                with open(webhook_config_path, 'r') as f:
                    webhook_config = yaml.safe_load(f)
                
                if webhook_config and 'webhooks' in webhook_config:
                    default_webhook = webhook_config['webhooks'].get('default')
                    if default_webhook and 'events' in default_webhook:
                        events = default_webhook['events']
                        print(f"ℹ️ Using events from webhook config: {', '.join(events)}")
        
        # Set default events if still not found
        if not events:
            if provider_name == 'github':
                events = ['push', 'pull_request', 'issues']
            elif provider_name == 'stripe':
                events = ['payment_intent.succeeded', 'payment_intent.failed', 'customer.created']
            else:
                events = ['event']
                print(f"⚠️ No events specified. Using generic event handler.")
        
        # Set class name
        class_name = args.class_name or f"{provider_name.title()}WebhookHandler"
        
        # Generate the handler class
        handler_code = generate_handler_class(provider_name, events, class_name)
        
        # Set output file
        if args.output_file:
            output_file = Path(args.output_file)
        else:
            output_file = Path(f"./{provider_name}_webhook_handler.py")
        
        # Write to file
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            f.write(handler_code)
        
        print(f"✅ Generated webhook handler class: {output_file}")
        print(f"   Class name: {class_name}")
        print(f"   Provider: {provider_name}")
        print(f"   Events: {', '.join(events)}")
        
        # Show usage example
        print(f"\n📖 Usage example:")
        print(f"```python")
        print(f"from {output_file.stem} import {class_name}")
        print(f"")
        print(f"# Instantiate the handler")
        print(f"handler = {class_name}()")
        print(f"```")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error generating webhook handler: {str(e)}")
        return 1


def generate_handler_class(provider: str, events: List[str], class_name: str) -> str:
    """Generate webhook handler class code."""
    
    # Start building the class
    code_lines = [
        '#!/usr/bin/env python3',
        '"""',
        f'Generated {class_name} for {provider} webhooks',
        '',
        f'This file was auto-generated by smart-api-integrations.',
        f'Provider: {provider}',
        '"""',
        '',
        'import logging',
        'from typing import Dict, Any, Optional',
        'from smart_api_integrations.webhooks import WebhookHandler, WebhookEvent',
        '',
        '# Set up logging',
        'logger = logging.getLogger(__name__)',
        '',
        '',
        f'class {class_name}(WebhookHandler):',
        f'    """',
        f'    {provider.title()} webhook handler.',
        f'    ',
        f'    Handles events: {", ".join(events)}',
        f'    """',
        f'    ',
        f'    provider = \'{provider}\'',
        f'    ',
    ]
    
    # Add event handler methods
    for event in events:
        method_name = f"on_{event.replace('.', '_')}"
        
        method_lines = [
            f'    def {method_name}(self, event: WebhookEvent) -> Dict[str, Any]:',
            f'        """',
            f'        Handle {provider} {event} event.',
            f'        ',
            f'        Args:',
            f'            event: The webhook event',
            f'        ',
            f'        Returns:',
            f'            Response data',
            f'        """',
            f'        # Access event data',
            f'        payload = event.payload',
            f'        ',
            f'        # Log the event',
            f'        logger.info(f"Received {provider} {event} event: {{event.id}}")',
            f'        ',
            f'        # TODO: Add your business logic here',
            f'        ',
            f'        # Return success response',
            f'        return self.success_response({{',
            f'            \'event_type\': \'{event}\',',
            f'            \'processed\': True',
            f'        }})',
            f'',
            f'',
        ]
        
        code_lines.extend(method_lines)
    
    # Add example usage
    code_lines.extend([
        '# Example usage',
        'if __name__ == "__main__":',
        f'    # Instantiate the handler',
        f'    handler = {class_name}()',
        f'    print(f"Created {class_name} for {provider} webhooks")',
        f'    print(f"Supported events: {", ".join(events)}")',
    ])
    
    return '\n'.join(code_lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Generate a webhook handler class for a provider'
    )
    register_command(parser.add_subparsers())
    args = parser.parse_args()
    
    if hasattr(args, 'func'):
        sys.exit(args.func(args))
    else:
        parser.print_help()
        sys.exit(1) 