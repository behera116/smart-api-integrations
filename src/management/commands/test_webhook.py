"""
Management command to test webhook handlers.

This command allows you to test your webhook handlers by sending
sample payloads without needing to set up actual webhooks.
"""

import json
import os
from datetime import datetime, timezone
from django.core.management.base import BaseCommand, CommandError
from django.http import HttpRequest

from ...core.webhook_registry import get_webhook_registry
from ...core.webhook_schema import WebhookEvent


class Command(BaseCommand):
    help = 'Test webhook handlers with sample payloads'

    def add_arguments(self, parser):
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

    def handle(self, *args, **options):
        provider = options['provider']
        event_type = options['event_type']
        webhook_name = options['webhook_name']
        
        # Get webhook registry and processor
        registry = get_webhook_registry()
        processor_key = f"{provider}:{webhook_name}"
        
        try:
            processor = registry.get_processor(processor_key)
            if not processor:
                processor = registry.create_processor(provider, webhook_name)
        except ValueError as e:
            raise CommandError(f"Failed to get processor for {processor_key}: {e}")
        
        # Handle list handlers option
        if options['list_handlers']:
            self.list_handlers(processor, provider, webhook_name)
            return
        
        # Handle sample payload option
        if options['sample_payload']:
            self.show_sample_payload(provider, event_type)
            return
        
        # Get payload data
        payload_data = self.get_payload_data(options, provider, event_type)
        
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
        self.stdout.write(f"Testing webhook: {provider}:{webhook_name}")
        self.stdout.write(f"Event type: {event_type}")
        self.stdout.write(f"Event ID: {event.id}")
        self.stdout.write("=" * 50)
        
        try:
            response = processor.process(event)
            
            if response.success:
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Webhook processed successfully!")
                )
                self.stdout.write(f"Status Code: {response.status_code}")
                if response.message:
                    self.stdout.write(f"Message: {response.message}")
                if response.data:
                    self.stdout.write(f"Response Data: {json.dumps(response.data, indent=2)}")
            else:
                self.stdout.write(
                    self.style.ERROR(f"❌ Webhook processing failed!")
                )
                self.stdout.write(f"Status Code: {response.status_code}")
                self.stdout.write(f"Error: {response.message}")
                if response.data:
                    self.stdout.write(f"Error Data: {json.dumps(response.data, indent=2)}")
                    
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"💥 Exception during processing: {e}")
            )
            raise
    
    def list_handlers(self, processor, provider, webhook_name):
        """List all registered handlers for the processor."""
        self.stdout.write(f"Handlers for {provider}:{webhook_name}")
        self.stdout.write("=" * 40)
        
        if not processor.handlers:
            self.stdout.write(self.style.WARNING("No handlers registered"))
            return
        
        for event_type, handlers in processor.handlers.items():
            self.stdout.write(f"📧 {event_type}:")
            for i, handler in enumerate(handlers, 1):
                handler_name = getattr(handler, '__name__', str(handler))
                self.stdout.write(f"   {i}. {handler_name}")
        
        self.stdout.write(f"\nTotal event types: {len(processor.handlers)}")
        total_handlers = sum(len(handlers) for handlers in processor.handlers.values())
        self.stdout.write(f"Total handlers: {total_handlers}")
        
        if processor.middleware:
            self.stdout.write(f"Middleware: {len(processor.middleware)} registered")
    
    def get_payload_data(self, options, provider, event_type):
        """Get payload data from file, string, or generate sample."""
        if options['payload_file']:
            return self.load_payload_from_file(options['payload_file'])
        elif options['payload']:
            return self.parse_payload_string(options['payload'])
        else:
            return self.generate_sample_payload(provider, event_type)
    
    def load_payload_from_file(self, file_path):
        """Load payload from JSON file."""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise CommandError(f"Payload file not found: {file_path}")
        except json.JSONDecodeError as e:
            raise CommandError(f"Invalid JSON in payload file: {e}")
    
    def parse_payload_string(self, payload_string):
        """Parse payload from JSON string."""
        try:
            return json.loads(payload_string)
        except json.JSONDecodeError as e:
            raise CommandError(f"Invalid JSON in payload string: {e}")
    
    def generate_sample_payload(self, provider, event_type):
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
                            'metadata': {
                                'order_id': 'order_123',
                                'user_id': 'user_456'
                            }
                        }
                    }
                },
                'customer.created': {
                    'id': 'evt_test_webhook',
                    'object': 'event',
                    'type': 'customer.created',
                    'data': {
                        'object': {
                            'id': 'cus_test_12345',
                            'object': 'customer',
                            'email': 'test@example.com',
                            'name': 'Test Customer'
                        }
                    }
                }
            },
            'github': {
                'push': {
                    'ref': 'refs/heads/main',
                    'repository': {
                        'name': 'test-repo',
                        'full_name': 'user/test-repo'
                    },
                    'commits': [
                        {
                            'id': 'abc123',
                            'message': 'Test commit',
                            'author': {'name': 'Test User', 'email': 'test@example.com'}
                        }
                    ]
                },
                'pull_request': {
                    'action': 'opened',
                    'pull_request': {
                        'number': 42,
                        'title': 'Test PR',
                        'state': 'open'
                    }
                }
            },
            'slack': {
                'message': {
                    'event': {
                        'type': 'message',
                        'channel': 'C1234567890',
                        'user': 'U1234567890',
                        'text': 'Hello, world!',
                        'ts': '1234567890.123456'
                    }
                }
            }
        }
        
        provider_samples = samples.get(provider, {})
        if event_type in provider_samples:
            return provider_samples[event_type]
        
        # Generic sample payload
        return {
            'id': f'test_{event_type}',
            'type': event_type,
            'data': {
                'test': True,
                'timestamp': datetime.now().isoformat(),
                'provider': provider
            }
        }
    
    def show_sample_payload(self, provider, event_type):
        """Show sample payload for an event type."""
        payload = self.generate_sample_payload(provider, event_type)
        
        self.stdout.write(f"Sample payload for {provider}:{event_type}")
        self.stdout.write("=" * 50)
        self.stdout.write(json.dumps(payload, indent=2))
        self.stdout.write("\nTo test with this payload, use:")
        self.stdout.write(f"python manage.py test_webhook {provider} {event_type} --payload '{json.dumps(payload)}'") 