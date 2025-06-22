"""
Command to test Smart API system.

Usage: 
    smart-api-integrations test
    smart-api-integrations test --provider github
    smart-api-integrations test --list-providers
"""

import sys
import argparse
from typing import List, Dict, Any


def register_command(subparsers):
    """Register the command with the given subparsers."""
    parser = subparsers.add_parser(
        'test',
        help='Test Smart API integration system with examples',
        description='Test Smart API integration system with examples'
    )
    
    parser.add_argument(
        '--provider',
        type=str,
        help='Test specific provider only',
    )
    parser.add_argument(
        '--list-providers',
        action='store_true',
        help='List available providers only',
    )
    parser.add_argument(
        '--verbosity',
        type=int,
        default=1,
        choices=[0, 1, 2],
        help='Verbosity level (0=minimal, 1=normal, 2=verbose)'
    )
    
    parser.set_defaults(func=command_handler)
    return parser


def command_handler(args):
    """Handle the test command."""
    try:
        if args.list_providers:
            try:
                from smart_api_integrations.core.registry import list_providers, get_provider_info
            except ImportError:
                # For local development when package is not installed
                import importlib.util
                import sys
                from pathlib import Path
                
                # Add parent directory to path if running as script
                if __name__ == "__main__":
                    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
                
                from src.core.registry import list_providers, get_provider_info
            
            providers = list_providers()
            print(f'Found {len(providers)} providers:')
            
            for provider_name in providers:
                try:
                    provider_info = get_provider_info(provider_name)
                    endpoints = provider_info.get('endpoints', [])
                    print(f'  • {provider_name} ({len(endpoints)} endpoints)')
                    
                    if args.verbosity >= 2:
                        for endpoint_name in endpoints:
                            print(f'    - {endpoint_name}')
                except Exception as e:
                    print(f'    Error loading {provider_name}: {e}')
        
        elif args.provider:
            # Test specific provider
            provider_name = args.provider
            test_provider(provider_name)
        
        else:
            # Run all examples
            print('Running Smart API examples...')
            try:
                from smart_api_integrations.examples import run_all_examples
            except ImportError:
                # For local development when package is not installed
                import importlib.util
                import sys
                from pathlib import Path
                
                # Add parent directory to path if running as script
                if __name__ == "__main__":
                    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
                
                from src.examples import run_all_examples
            
            run_all_examples()
        
        return 0
    
    except Exception as e:
        print(f'Smart API test failed: {e}')
        return 1


def test_provider(provider_name):
    """Test a specific provider."""
    try:
        try:
            from smart_api_integrations.core.registry import get_client, get_provider_info
        except ImportError:
            # For local development when package is not installed
            import importlib.util
            import sys
            from pathlib import Path
            
            # Add parent directory to path if running as script
            if __name__ == "__main__":
                sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
            
            from src.core.registry import get_client, get_provider_info
        
        # Check if provider exists
        provider_info = get_provider_info(provider_name)
        endpoints = provider_info.get('endpoints', [])
        print(f'Testing provider: {provider_name}')
        print(f'Available endpoints: {endpoints}')
        
        # Create client (without auth for basic test)
        client = get_client(provider_name)
        
        print(f'✅ Provider {provider_name} loaded successfully')
        
    except Exception as e:
        print(f'❌ Provider {provider_name} test failed: {e}')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Test Smart API integration system with examples'
    )
    register_command(parser.add_subparsers())
    args = parser.parse_args()
    
    if hasattr(args, 'func'):
        sys.exit(args.func(args))
    else:
        parser.print_help()
        sys.exit(1)
