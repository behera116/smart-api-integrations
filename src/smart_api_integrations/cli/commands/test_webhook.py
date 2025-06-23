"""
CLI command for testing webhooks.
"""

import json
import logging
import sys
import click
import requests
from pathlib import Path
import hmac
import hashlib
from datetime import datetime, timezone
import argparse

from smart_api_integrations.core.webhook_registry import get_webhook_registry
from smart_api_integrations.core.webhook_schema import WebhookEvent

logger = logging.getLogger(__name__)


def register_command(subparsers: argparse._SubParsersAction) -> None:
    """Register the command with the given subparsers."""
    parser = subparsers.add_parser(
        "test-webhook",
        help="Test a webhook by simulating an event",
        description="Test a webhook by simulating an event. If --url is provided, sends a real HTTP request to the specified URL. Otherwise, processes the webhook locally using the registered handlers."
    )
    
    parser.add_argument(
        "provider",
        help="Provider name"
    )
    
    parser.add_argument(
        "--webhook-name", "-w",
        default="default",
        help="Name of the webhook to test"
    )
    
    parser.add_argument(
        "--event", "-e",
        required=True,
        help="Event type to simulate"
    )
    
    parser.add_argument(
        "--payload", "-p",
        help="Path to JSON file with payload data"
    )
    
    parser.add_argument(
        "--url", "-u",
        help="URL to send the webhook to"
    )
    
    parser.add_argument(
        "--secret", "-s",
        help="Secret to use for signature verification"
    )
    
    parser.set_defaults(func=command_func)


def command_func(args: argparse.Namespace) -> int:
    """Execute the command."""
    try:
        test_webhook(
            args.provider,
            args.webhook_name,
            args.event,
            args.payload,
            args.url,
            args.secret
        )
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


@click.command("test-webhook")
@click.argument("provider", required=True)
@click.option("--webhook-name", "-w", default="default", help="Name of the webhook to test")
@click.option("--event", "-e", required=True, help="Event type to simulate")
@click.option("--payload", "-p", help="Path to JSON file with payload data")
@click.option("--url", "-u", help="URL to send the webhook to")
@click.option("--secret", "-s", help="Secret to use for signature verification")
def test_webhook(provider, webhook_name, event, payload, url, secret):
    """
    Test a webhook by simulating an event.
    
    If --url is provided, sends a real HTTP request to the specified URL.
    Otherwise, processes the webhook locally using the registered handlers.
    
    Examples:
        smart-api-integrations test-webhook stripe --event payment.succeeded --payload payload.json
        smart-api-integrations test-webhook github --event push --url http://localhost:8000/webhooks/github/
    """
    try:
        # Get the webhook registry
        registry = get_webhook_registry()
        
        # Get the webhook processor
        processor_key = f"{provider}:{webhook_name}"
        processor = registry.get_processor(processor_key)
        
        if not processor:
            click.echo(f"No webhook processor found for {processor_key}")
            return
        
        # Load payload data
        payload_data = {}
        if payload:
            try:
                with open(payload, 'r') as f:
                    payload_data = json.load(f)
            except Exception as e:
                click.echo(f"Error loading payload file: {e}")
                return
        
        # Add event type if not present
        if 'type' not in payload_data:
            payload_data['type'] = event
        
        # Add event ID if not present
        if 'id' not in payload_data:
            payload_data['id'] = f"evt_{int(datetime.now(timezone.utc).timestamp())}"
        
        # Convert payload to JSON string
        payload_json = json.dumps(payload_data)
        payload_bytes = payload_json.encode('utf-8')
        
        # If URL is provided, send HTTP request
        if url:
            headers = {
                'Content-Type': 'application/json',
            }
            
            # Add signature if secret is provided
            if secret:
                signature = hmac.new(
                    secret.encode('utf-8'),
                    payload_bytes,
                    hashlib.sha256
                ).hexdigest()
                headers[processor.config.signature_header] = f"sha256={signature}"
            
            # Send request
            click.echo(f"Sending webhook to {url}")
            click.echo(f"Event: {event}")
            click.echo(f"Payload: {payload_json}")
            
            response = requests.post(url, data=payload_bytes, headers=headers)
            
            click.echo(f"Response status: {response.status_code}")
            try:
                click.echo(f"Response body: {json.dumps(response.json(), indent=2)}")
            except:
                click.echo(f"Response body: {response.text}")
                
        # Otherwise, process locally
        else:
            # Create event
            webhook_event = WebhookEvent(
                id=payload_data.get('id', f"evt_{int(datetime.now(timezone.utc).timestamp())}"),
                type=event,
                provider=provider,
                webhook_name=webhook_name,
                payload=payload_data,
                headers={},
                timestamp=datetime.now(timezone.utc),
                raw_body=payload_bytes
            )
            
            # Process event
            click.echo(f"Processing webhook locally")
            click.echo(f"Event: {event}")
            click.echo(f"Payload: {payload_json}")
            
            response = processor.process(webhook_event)
            
            click.echo(f"Response: {json.dumps(response.dict(), indent=2)}")
        
    except Exception as e:
        click.echo(f"Error testing webhook: {e}")
        logger.exception("Error testing webhook")
