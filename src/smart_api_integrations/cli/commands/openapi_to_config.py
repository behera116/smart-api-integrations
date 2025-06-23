"""
Command to convert OpenAPI specifications to config.yaml files.
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path for local development
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from src.smart_api_integrations.cli.openapi_converter import convert_openapi_to_config


def register_command(subparsers: argparse._SubParsersAction) -> None:
    """Register the command with the given subparsers."""
    parser = subparsers.add_parser(
        "openapi-to-config",
        help="Convert OpenAPI specifications to config.yaml files",
        description="Convert OpenAPI specifications (JSON or YAML) to Smart API Integrations config.yaml files."
    )
    
    parser.add_argument(
        "openapi_path",
        help="Path to the OpenAPI specification file or URL"
    )
    
    parser.add_argument(
        "--output-dir", "-o",
        help="Directory to save the config.yaml file (defaults to same directory as openapi_path)"
    )
    
    parser.add_argument(
        "--provider-name", "-n",
        help="Name of the provider (defaults to filename without extension)"
    )
    
    parser.set_defaults(func=command_func)


def command_func(args: argparse.Namespace) -> int:
    """Execute the command."""
    try:
        config_file = convert_openapi_to_config(
            args.openapi_path,
            args.output_dir,
            args.provider_name
        )
        print(f"Successfully generated config.yaml at: {config_file}")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1 