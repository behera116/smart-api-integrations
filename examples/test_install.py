#!/usr/bin/env python3
"""
Test script to verify the installation of smart-api-integrations.
"""

import sys

try:
    import smart_api_integrations
    print(f"smart-api-integrations version: {smart_api_integrations.__version__ if hasattr(smart_api_integrations, '__version__') else 'unknown'}")
    print("Available dependencies:")
    deps = smart_api_integrations.check_dependencies()
    for dep, available in deps.items():
        print(f"  - {dep}: {'✅' if available else '❌'}")
    print("\nInstallation successful! 🎉")
    sys.exit(0)
except ImportError as e:
    print(f"Error importing smart-api-integrations: {e}")
    print("\nInstallation failed. 😢")
    sys.exit(1) 