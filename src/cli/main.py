#!/usr/bin/env python3
"""
Smart API Integrations CLI

Main entry point for the Smart API Integrations command-line interface.
"""

import sys
import argparse
from typing import List, Optional

from .commands import (
    add_provider,
    add_endpoints,
    test_webhook,
    add_webhook,
    generate_type_stubs,
    generate_client,
    generate_webhook_handler,
    smart_api_test
)


def main(args: Optional[List[str]] = None) -> int:
    """Main entry point for the CLI."""
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(
        prog="smart-api-integrations",
        description="Smart API Integrations CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"Smart API Integrations v{__import__('smart_api_integrations.cli').__version__}"
    )

    subparsers = parser.add_subparsers(
        title="commands",
        dest="command",
        help="Command to run"
    )
    
    # Register commands
    add_provider.register_command(subparsers)
    add_endpoints.register_command(subparsers)
    add_webhook.register_command(subparsers)
    test_webhook.register_command(subparsers)
    generate_type_stubs.register_command(subparsers)
    generate_client.register_command(subparsers)
    generate_webhook_handler.register_command(subparsers)
    smart_api_test.register_command(subparsers)
    
    # Parse arguments
    parsed_args = parser.parse_args(args)
    
    # If no command is specified, show help
    if not parsed_args.command:
        parser.print_help()
        return 1
    
    # Execute the command
    return parsed_args.func(parsed_args)


if __name__ == "__main__":
    sys.exit(main()) 