"""
Command to test webhook handlers.

This command allows you to test your webhook handlers by sending
sample payloads without needing to set up actual webhooks.

Usage:
    smart-api-integrations test-webhook github push
    smart-api-integrations test-webhook stripe payment_intent.succeeded --payload-file ./payload.json
"""

import json
import os
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List

try:
    from smart_api_integrations.core.webhook_registry import get_webhook_registry
    from smart_api_integrations.core.webhook_schema import WebhookEvent
except ImportError:
    # For local development when package is not installed
    import importlib.util
    import sys
    
    # Add parent directory to path if running as script
    if __name__ == "__main__":
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    
    from src.core.webhook_registry import get_webhook_registry
    from src.core.webhook_schema import WebhookEvent


def register_command(subparsers):
    """Register the command with the given subparsers."""
    parser = subparsers.add_parser(
        'test-webhook',
        help='Test webhook handlers with sample payloads',
        description='Test webhook handlers with sample payloads'
    )
    
    parser.add_argument(
        'provider',
        type=str,
        help='Provider name (e.g., stripe, github, slack)'
    )
    
    parser.add_argument(
        'event_type',
        type=str,
        help='Event type to test (e.g., payment_intent.succeeded)'
    )
    
    parser.add_argument(
        '--webhook-name',
        type=str,
        default='default',
        help='Webhook name (default: default)'
    )
    
    parser.add_argument(
        '--payload-file',
        type=str,
        help='Path to JSON file containing webhook payload'
    )
    
    parser.add_argument(
        '--payload',
        type=str,
        help='JSON string containing webhook payload'
    )
    
    parser.add_argument(
        '--list-handlers',
        action='store_true',
        help='List all registered handlers for the provider'
    )
    
    parser.add_argument(
        '--sample-payload',
        action='store_true',
        help='Generate and display a sample payload for the event type'
    )
    
    parser.set_defaults(func=command_handler)
    return parser


def command_handler(args):
    """Handle the test-webhook command."""
    try:
        provider = args.provider
        event_type = args.event_type
        webhook_name = args.webhook_name
        
        # Get webhook registry and processor
        registry = get_webhook_registry()
        processor_key = f"{provider}:{webhook_name}"
        
        try:
            processor = registry.get_processor(processor_key)
            if not processor:
                processor = registry.create_processor(provider, webhook_name)
        except ValueError as e:
            print(f"Failed to get processor for {processor_key}: {e}")
            return 1
        
        # Handle list handlers option
        if args.list_handlers:
            list_handlers(processor, provider, webhook_name)
            return 0
        
        # Handle sample payload option
        if args.sample_payload:
            show_sample_payload(provider, event_type)
            return 0
        
        # Get payload data
        payload_data = get_payload_data(args, provider, event_type)
        
        # Create webhook event
        event = WebhookEvent(
            id=f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            type=event_type,
            provider=provider,
            webhook_name=webhook_name,
            payload=payload_data,
            headers={'X-Test-Webhook': 'true'},
            timestamp=datetime.now(timezone.utc),
            verified=True
        )
        
        # Process the event
        print(f"Testing webhook: {provider}:{webhook_name}")
        print(f"Event type: {event_type}")
        print(f"Event ID: {event.id}")
        print("=" * 50)
        
        try:
            response = processor.process(event)
            
            if response.success:
                print(f"✅ Webhook processed successfully!")
                print(f"Status Code: {response.status_code}")
                if response.message:
                    print(f"Message: {response.message}")
                if response.data:
                    print(f"Response Data: {json.dumps(response.data, indent=2)}")
            else:
                print(f"❌ Webhook processing failed!")
                print(f"Status Code: {response.status_code}")
                print(f"Error: {response.message}")
                if response.data:
                    print(f"Error Data: {json.dumps(response.data, indent=2)}")
                    
            return 0 if response.success else 1
                    
        except Exception as e:
            print(f"💥 Exception during processing: {e}")
            return 1
    
    except Exception as e:
        print(f"Error testing webhook: {str(e)}")
        return 1


def list_handlers(processor, provider, webhook_name):
    """List all registered handlers for the processor."""
    print(f"Handlers for {provider}:{webhook_name}")
    print("=" * 40)
    
    if not processor.handlers:
        print("No handlers registered")
        return
    
    for event_type, handlers in processor.handlers.items():
        print(f"📧 {event_type}:")
        for i, handler in enumerate(handlers, 1):
            handler_name = getattr(handler, '__name__', str(handler))
            print(f"   {i}. {handler_name}")
    
    print(f"\nTotal event types: {len(processor.handlers)}")
    total_handlers = sum(len(handlers) for handlers in processor.handlers.values())
    print(f"Total handlers: {total_handlers}")
    
    if processor.middleware:
        print(f"Middleware: {len(processor.middleware)} registered")


def get_payload_data(args, provider, event_type):
    """Get payload data from file, string, or generate sample."""
    if args.payload_file:
        return load_payload_from_file(args.payload_file)
    elif args.payload:
        return parse_payload_string(args.payload)
    else:
        return generate_sample_payload(provider, event_type)


def load_payload_from_file(file_path):
    """Load payload from JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise ValueError(f"Payload file not found: {file_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in payload file: {e}")


def parse_payload_string(payload_string):
    """Parse payload from JSON string."""
    try:
        return json.loads(payload_string)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in payload string: {e}")


def generate_sample_payload(provider, event_type):
    """Generate sample payload based on provider and event type."""
    samples = {
        'stripe': {
            'payment_intent.succeeded': {
                'id': 'evt_test_webhook',
                'object': 'event',
                'type': 'payment_intent.succeeded',
                'data': {
                    'object': {
                        'id': 'pi_test_12345',
                        'object': 'payment_intent',
                        'amount': 2000,
                        'currency': 'usd',
                        'status': 'succeeded',
                        'customer': 'cus_test_12345',
                        'created': int(datetime.now().timestamp()),
                        'metadata': {
                            'order_id': 'test_order_123'
                        }
                    }
                }
            },
            'charge.succeeded': {
                'id': 'evt_test_webhook',
                'object': 'event',
                'type': 'charge.succeeded',
                'data': {
                    'object': {
                        'id': 'ch_test_12345',
                        'object': 'charge',
                        'amount': 2000,
                        'currency': 'usd',
                        'status': 'succeeded',
                        'customer': 'cus_test_12345',
                        'created': int(datetime.now().timestamp()),
                        'metadata': {
                            'order_id': 'test_order_123'
                        }
                    }
                }
            }
        },
        'github': {
            'push': {
                'ref': 'refs/heads/main',
                'repository': {
                    'name': 'test-repo',
                    'full_name': 'test-user/test-repo',
                    'owner': {
                        'login': 'test-user'
                    }
                },
                'commits': [
                    {
                        'id': 'test_commit_id',
                        'message': 'Test commit message',
                        'author': {
                            'name': 'Test User',
                            'email': 'test@example.com'
                        },
                        'timestamp': datetime.now().isoformat()
                    }
                ]
            },
            'pull_request': {
                'action': 'opened',
                'number': 123,
                'pull_request': {
                    'title': 'Test PR',
                    'body': 'This is a test pull request',
                    'user': {
                        'login': 'test-user'
                    },
                    'head': {
                        'ref': 'feature-branch'
                    },
                    'base': {
                        'ref': 'main'
                    }
                },
                'repository': {
                    'name': 'test-repo',
                    'full_name': 'test-user/test-repo'
                }
            }
        }
    }
    
    # Get sample for provider and event type
    provider_samples = samples.get(provider, {})
    sample = provider_samples.get(event_type)
    
    if not sample:
        # Generate generic sample if specific one not found
        sample = {
            'event_type': event_type,
            'provider': provider,
            'timestamp': datetime.now().isoformat(),
            'data': {
                'id': f'test_{provider}_{event_type}',
                'test': True
            }
        }
    
    return sample


def show_sample_payload(provider, event_type):
    """Generate and display a sample payload for the event type."""
    sample = generate_sample_payload(provider, event_type)
    
    print(f"Sample payload for {provider}:{event_type}")
    print("=" * 50)
    print(json.dumps(sample, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Test webhook handlers with sample payloads'
    )
    register_command(parser.add_subparsers())
    args = parser.parse_args()
    
    if hasattr(args, 'func'):
        sys.exit(args.func(args))
    else:
        parser.print_help()
        sys.exit(1)
