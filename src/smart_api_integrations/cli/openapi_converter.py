"""
OpenAPI to Config YAML Converter

This tool converts OpenAPI specifications (JSON or YAML) to Smart API Integrations config.yaml files.
"""

import os
import sys
import yaml
import json
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

# Add parent directory to path for local development
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.smart_api_integrations.core.loader import ConfigLoader
from src.smart_api_integrations.core.schema import ProviderConfig


def convert_openapi_to_config(
    openapi_path: str, 
    output_dir: Optional[str] = None,
    provider_name: Optional[str] = None
) -> str:
    """
    Convert an OpenAPI specification to a config.yaml file.
    
    Args:
        openapi_path: Path to the OpenAPI specification file or URL
        output_dir: Directory to save the config.yaml file (defaults to same directory as openapi_path)
        provider_name: Name of the provider (defaults to filename without extension)
    
    Returns:
        Path to the generated config.yaml file
    """
    loader = ConfigLoader()
    
    # Determine if it's a URL or file path
    if openapi_path.startswith(('http://', 'https://')):
        # It's a URL
        if not provider_name:
            # Extract provider name from the last part of the URL
            provider_name = openapi_path.split('/')[-1].split('.')[0]
        
        # Load from URL
        config = loader.load_remote_openapi_config(provider_name, openapi_path)
    else:
        # It's a file path
        openapi_file = Path(openapi_path)
        
        if not provider_name:
            # Use the file name without extension as provider name
            provider_name = openapi_file.stem
        
        # Load the file
        if openapi_file.suffix.lower() in ['.yaml', '.yml']:
            with open(openapi_file, 'r') as f:
                openapi_spec = yaml.safe_load(f)
        elif openapi_file.suffix.lower() == '.json':
            with open(openapi_file, 'r') as f:
                openapi_spec = json.load(f)
        else:
            raise ValueError(f"Unsupported file extension: {openapi_file.suffix}")
        
        # Process the OpenAPI spec
        config = loader._process_openapi_spec(openapi_spec, provider_name)
    
    # Determine output directory
    if output_dir:
        output_path = Path(output_dir) / provider_name
    else:
        if openapi_path.startswith(('http://', 'https://')):
            # For URLs, use current directory
            output_path = Path.cwd() / provider_name
        else:
            # For files, use the same directory as the input file
            output_path = Path(openapi_path).parent / provider_name
    
    # Create the output directory if it doesn't exist
    output_path.mkdir(exist_ok=True, parents=True)
    
    # Convert the config to a dictionary
    config_dict = config.dict()
    
    # Clean up the dictionary to make it more YAML-friendly
    config_dict = _clean_config_dict(config_dict)
    
    # Write the config.yaml file
    config_file = output_path / "config.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)
    
    return str(config_file)


def _clean_config_dict(config_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean up the config dictionary to make it more YAML-friendly.
    
    Args:
        config_dict: The config dictionary
    
    Returns:
        The cleaned config dictionary
    """
    # Remove None values
    result = {k: v for k, v in config_dict.items() if v is not None}
    
    # Handle nested dictionaries
    for key, value in result.items():
        if isinstance(value, dict):
            result[key] = _clean_config_dict(value)
        elif isinstance(value, list):
            result[key] = [_clean_dict(item) if isinstance(item, dict) else item for item in value]
    
    # Convert Pydantic enums to strings
    if 'method' in result and hasattr(result['method'], 'value'):
        result['method'] = result['method'].value
    
    if 'type' in result and hasattr(result['type'], 'value'):
        result['type'] = result['type'].value
    
    # Handle endpoints specially to organize them better
    if 'endpoints' in result:
        endpoints = result['endpoints']
        for endpoint_name, endpoint_config in endpoints.items():
            # Clean up each endpoint config
            endpoints[endpoint_name] = _clean_dict(endpoint_config)
    
    return result


def _clean_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean up a dictionary recursively.
    
    Args:
        d: The dictionary to clean
    
    Returns:
        The cleaned dictionary
    """
    if not isinstance(d, dict):
        return d
    
    result = {k: v for k, v in d.items() if v is not None}
    
    for key, value in result.items():
        if isinstance(value, dict):
            result[key] = _clean_dict(value)
        elif isinstance(value, list):
            result[key] = [_clean_dict(item) if isinstance(item, dict) else item for item in value]
        elif hasattr(value, 'value'):  # Handle enums
            result[key] = value.value
    
    return result


def main():
    """Main entry point for the OpenAPI converter CLI."""
    parser = argparse.ArgumentParser(description='Convert OpenAPI specifications to config.yaml files')
    parser.add_argument('openapi_path', help='Path to the OpenAPI specification file or URL')
    parser.add_argument('--output-dir', '-o', help='Directory to save the config.yaml file')
    parser.add_argument('--provider-name', '-n', help='Name of the provider')
    
    args = parser.parse_args()
    
    try:
        config_file = convert_openapi_to_config(
            args.openapi_path,
            args.output_dir,
            args.provider_name
        )
        print(f"Successfully generated config.yaml at: {config_file}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main() 