#!/usr/bin/env python3
"""
Release automation script for Smart API Integrations.
"""

import argparse
import subprocess
import sys
from pathlib import Path
import re

def run_command(cmd, cwd=None):
    """Run a command and return the result."""
    print(f"🔧 Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    if result.returncode != 0:
        print(f"❌ Command failed: {cmd}")
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result.stdout.strip()

def get_current_version():
    """Get current version from pyproject.toml"""
    pyproject_path = Path("pyproject.toml")
    content = pyproject_path.read_text()
    match = re.search(r'version = "([^"]+)"', content)
    if match:
        return match.group(1)
    raise ValueError("Could not find version in pyproject.toml")

def update_version(old_version, new_version):
    """Update version in pyproject.toml and __init__.py"""
    # Update pyproject.toml
    pyproject_path = Path("pyproject.toml")
    content = pyproject_path.read_text()
    content = content.replace(
        f'version = "{old_version}"',
        f'version = "{new_version}"'
    )
    pyproject_path.write_text(content)
    
    # Update __init__.py
    init_path = Path("src/__init__.py")
    content = init_path.read_text()
    content = content.replace(
        f'__version__ = "{old_version}"',
        f'__version__ = "{new_version}"'
    )
    init_path.write_text(content)
    
    print(f"✅ Updated version from {old_version} to {new_version}")

def update_changelog(version):
    """Update CHANGELOG.md with new version"""
    changelog_path = Path("CHANGELOG.md")
    if not changelog_path.exists():
        print("⚠️  CHANGELOG.md not found, skipping changelog update")
        return
    
    content = changelog_path.read_text()
    
    # Add new version section after [Unreleased]
    unreleased_section = "## [Unreleased]"
    new_section = f"""## [Unreleased]

### Added
- 

### Fixed
- 

### Changed
- 

## [{version}] - 2024-06-22"""
    
    if unreleased_section in content:
        content = content.replace(unreleased_section, new_section)
        changelog_path.write_text(content)
        print(f"✅ Updated CHANGELOG.md with version {version}")
    else:
        print("⚠️  Could not find [Unreleased] section in CHANGELOG.md")

def validate_environment():
    """Validate that required tools are available"""
    required_tools = ["git", "python", "pip"]
    
    for tool in required_tools:
        try:
            run_command(f"which {tool}")
        except SystemExit:
            print(f"❌ Required tool '{tool}' not found")
            sys.exit(1)
    
    # Check if we're in a git repository
    try:
        run_command("git rev-parse --git-dir")
    except SystemExit:
        print("❌ Not in a git repository")
        sys.exit(1)
    
    print("✅ Environment validation passed")

def run_tests():
    """Run the test suite"""
    print("🧪 Running tests...")
    try:
        run_command("python -m pytest tests/ -v")
        print("✅ All tests passed")
    except SystemExit:
        print("❌ Tests failed")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            sys.exit(1)

def check_code_quality():
    """Check code formatting and type checking"""
    print("🔍 Checking code quality...")
    
    # Check if tools are available
    tools_available = True
    try:
        run_command("python -m black --version")
    except SystemExit:
        print("⚠️  black not available, skipping formatting check")
        tools_available = False
    
    try:
        run_command("python -m isort --version")
    except SystemExit:
        print("⚠️  isort not available, skipping import sorting check")
        tools_available = False
    
    if tools_available:
        try:
            run_command("python -m black --check src tests")
            run_command("python -m isort --check-only src tests")
            print("✅ Code formatting checks passed")
        except SystemExit:
            print("❌ Code formatting issues found")
            response = input("Continue anyway? (y/N): ")
            if response.lower() != 'y':
                sys.exit(1)

def build_package():
    """Build the package"""
    print("📦 Building package...")
    
    # Clean previous builds
    run_command("rm -rf dist/ build/ *.egg-info/")
    
    # Install build tool if not available
    try:
        run_command("python -m build --version")
    except SystemExit:
        print("Installing build tool...")
        run_command("pip install build")
    
    # Build package
    run_command("python -m build")
    
    # Verify build
    dist_files = list(Path("dist").glob("*"))
    if len(dist_files) < 2:
        print("❌ Build failed - expected wheel and source distribution")
        sys.exit(1)
    
    print("✅ Package built successfully")
    for file in dist_files:
        print(f"  📦 {file.name}")

def main():
    parser = argparse.ArgumentParser(description="Release Smart API Integrations")
    parser.add_argument("--version", required=True, help="Version to release (e.g., 0.1.1)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument("--skip-tests", action="store_true", help="Skip running tests")
    parser.add_argument("--skip-quality", action="store_true", help="Skip code quality checks")
    parser.add_argument("--no-git", action="store_true", help="Skip git operations")
    
    args = parser.parse_args()
    
    print(f"🚀 Releasing Smart API Integrations v{args.version}")
    
    if args.dry_run:
        print(f"🔍 DRY RUN: Would release version {args.version}")
        print("Steps that would be performed:")
        print("  1. Validate environment")
        print("  2. Run tests")
        print("  3. Check code quality")
        print("  4. Update version")
        print("  5. Update changelog")
        print("  6. Build package")
        print("  7. Commit and tag")
        return
    
    # Validate environment
    validate_environment()
    
    # Get current version
    current_version = get_current_version()
    print(f"📋 Current version: {current_version}")
    print(f"📋 New version: {args.version}")
    
    # Run tests
    if not args.skip_tests:
        run_tests()
    
    # Check code quality
    if not args.skip_quality:
        check_code_quality()
    
    # Update version
    update_version(current_version, args.version)
    
    # Update changelog
    update_changelog(args.version)
    
    # Build package
    build_package()
    
    # Git operations
    if not args.no_git:
        print("📝 Committing changes...")
        run_command("git add .")
        run_command(f"git commit -m 'Release v{args.version}'")
        run_command(f"git tag v{args.version}")
        print("✅ Changes committed and tagged")
    
    print(f"🎉 Release v{args.version} ready!")
    print("\nNext steps:")
    if not args.no_git:
        print(f"  1. git push origin main")
        print(f"  2. git push origin v{args.version}")
    print(f"  3. python -m twine upload dist/*")
    print(f"  4. Create GitHub release at: https://github.com/behera116/smart-api-integrations/releases/new")
    
    print(f"\nTo publish to PyPI:")
    print(f"  export TWINE_USERNAME=__token__")
    print(f"  export TWINE_PASSWORD=pypi-your-api-token-here")
    print(f"  python -m twine upload dist/*")

if __name__ == "__main__":
    main() 