#!/usr/bin/env python3
"""
Example script demonstrating how to use the OpenAPI converter.

This example shows how to:
1. Convert an OpenAPI specification to a config.yaml file
2. Use the generated config.yaml file with the UniversalAPIClient
"""

import os
import sys
import json
from pathlib import Path

# Add the parent directory to the path so we can import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.smart_api_integrations import UniversalAPIClient
from src.smart_api_integrations.cli.openapi_converter import convert_openapi_to_config


def main():
    """Main function to demonstrate the OpenAPI converter."""
    # Define the OpenAPI specification URL
    openapi_url = "https://petstore3.swagger.io/api/v3/openapi.json"
    
    # Define the provider name
    provider_name = "petstore"
    
    # Define the output directory
    output_dir = Path(__file__).parent / "generated"
    output_dir.mkdir(exist_ok=True)
    
    print(f"Converting OpenAPI specification from {openapi_url}...")
    
    # Convert the OpenAPI specification to a config.yaml file
    config_file = convert_openapi_to_config(
        openapi_url,
        output_dir=str(output_dir),
        provider_name=provider_name
    )
    
    print(f"Generated config.yaml at: {config_file}")
    
    # Print the first few lines of the config.yaml file
    with open(config_file, 'r') as f:
        lines = f.readlines()
        print("\nFirst 10 lines of the config.yaml file:")
        for line in lines[:10]:
            print(f"  {line.rstrip()}")
        print("  ...")
    
    # Now use the generated config.yaml file with the UniversalAPIClient
    print("\nCreating client from the generated config.yaml file...")
    
    # The provider directory is the directory containing the config.yaml file
    provider_dir = Path(config_file).parent.name
    
    # Create a client for the API
    client = UniversalAPIClient(provider_dir)
    
    # List available methods
    methods = client.list_available_methods()
    print(f"\nAvailable methods ({len(methods)}):")
    for method_name, description in list(methods.items())[:5]:  # Show first 5 methods
        print(f"  - {method_name}: {description[:50]}...")
    
    if len(methods) > 5:
        print(f"  ... and {len(methods) - 5} more methods")
    
    # Show help for a specific method
    method_name = "get_pet_by_id"  # This is the snake_case version of getPetById
    if method_name in methods:
        print(f"\nHelp for {method_name}:")
        print(client.get_method_help(method_name))
    
    print("\nThe client is now ready to use with the generated config.yaml file!")


if __name__ == "__main__":
    main() 