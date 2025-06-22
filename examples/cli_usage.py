#!/usr/bin/env python3
"""
Example script demonstrating how to use the Smart API Integrations CLI.

This script shows how to use the CLI both from the command line and from Python code.
"""

import os
import subprocess
from pathlib import Path

# Create directory for examples if it doesn't exist
os.makedirs("examples/output", exist_ok=True)

# Example 1: Using the CLI from the command line
print("Example 1: Using the CLI from the command line")
print("-" * 50)

try:
    # List available commands
    subprocess.run(["smart-api-integrations", "--help"], check=True)
    print("CLI command executed successfully")
except subprocess.CalledProcessError:
    print("Failed to execute CLI command")

print("\n")

# Example 2: Using the CLI with version flag
print("Example 2: Using the CLI with version flag")
print("-" * 50)

try:
    # Show version
    subprocess.run(["smart-api-integrations", "--version"], check=True)
    print("Version command executed successfully")
except subprocess.CalledProcessError:
    print("Failed to execute version command")

print("\n")

# Example 3: Creating a provider configuration
print("Example 3: Creating a provider configuration")
print("-" * 50)

# Create a test provider configuration
providers_dir = Path("examples/output/providers")
os.makedirs(providers_dir, exist_ok=True)

print(f"Creating a test provider configuration in {providers_dir}")
try:
    subprocess.run([
        "smart-api-integrations", 
        "add-provider", 
        "--name", "example", 
        "--base-url", "https://api.example.com",
        "--auth", "bearer",
        "--providers-dir", str(providers_dir),
        "--dry-run"
    ], check=True)
    
    print("Provider configuration created successfully")
except subprocess.CalledProcessError:
    print("Failed to create provider configuration")

print("\n")

# Example 4: Getting help for a specific command
print("Example 4: Getting help for a specific command")
print("-" * 50)

try:
    # Get help for add-endpoints command
    subprocess.run(["smart-api-integrations", "add-endpoints", "--help"], check=True)
    print("Help command executed successfully")
except subprocess.CalledProcessError:
    print("Failed to execute help command")

print("\nScript completed successfully!")
