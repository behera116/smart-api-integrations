# 📦 Publishing Guide

This guide walks you through publishing the Smart API Integrations package to PyPI.

## 🚀 Quick Publish (For Maintainers)

```bash
# 1. Update version and create release
python scripts/release.py --version 0.1.1

# 2. Build and publish
python -m build
python -m twine upload dist/*
```

## 📋 Prerequisites

### 1. Install Build Tools

```bash
# Install build and publishing dependencies
pip install build twine

# Or install dev dependencies
pip install -e ".[dev]"
```

### 2. Create PyPI Account

1. **Create account**: Go to [PyPI](https://pypi.org/account/register/)
2. **Verify email**: Check your email and verify your account
3. **Enable 2FA**: Go to Account Settings → Add 2FA (recommended)

### 3. Create API Token

1. Go to [PyPI Account Settings](https://pypi.org/manage/account/)
2. Scroll to "API tokens" section
3. Click "Add API token"
4. **Name**: `smart-api-integrations-upload`
5. **Scope**: Select "Entire account" (or specific project after first upload)
6. **Copy the token** - you'll need it for publishing

### 4. Configure Twine

Create `~/.pypirc`:

```ini
[distutils]
index-servers = pypi

[pypi]
username = __token__
password = pypi-your-api-token-here
```

**Or use environment variable:**

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-your-api-token-here
```

## 🔄 Release Process

### 1. Pre-Release Checklist

```bash
# ✅ Ensure all tests pass
pytest

# ✅ Check code formatting
black --check src tests
isort --check-only src tests

# ✅ Run type checking
mypy src

# ✅ Test package installation locally
pip install -e .
smart-api-integrations --version

# ✅ Test CLI functionality
smart-api-integrations list-providers
```

### 2. Update Version

Update version in these files:
- `pyproject.toml` → `version = "0.1.1"`
- `src/__init__.py` → `__version__ = "0.1.1"`

### 3. Update Changelog

Add new version to `CHANGELOG.md`:

```markdown
## [0.1.1] - 2024-06-23

### Added
- New feature description

### Fixed
- Bug fix description

### Changed
- Breaking change description
```

### 4. Commit and Tag

```bash
# Commit version changes
git add .
git commit -m "Release v0.1.1"

# Create and push tag
git tag v0.1.1
git push origin main
git push origin v0.1.1
```

### 5. Build Package

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info/

# Build source distribution and wheel
python -m build

# Verify build contents
ls -la dist/
# Should show:
# smart_api_integrations-0.1.1-py3-none-any.whl
# smart_api_integrations-0.1.1.tar.gz
```

### 6. Test Build Locally

```bash
# Test wheel installation
pip install dist/smart_api_integrations-0.1.1-py3-none-any.whl

# Test source distribution
pip install dist/smart_api_integrations-0.1.1.tar.gz

# Verify installation
python -c "import smart_api_integrations; print(smart_api_integrations.__version__)"
smart-api-integrations --version
```

### 7. Upload to Test PyPI (Optional)

```bash
# Upload to Test PyPI first
python -m twine upload --repository testpypi dist/*

# Test installation from Test PyPI
pip install --index-url https://test.pypi.org/simple/ smart-api-integrations

# Test functionality
python -c "from smart_api_integrations import UniversalAPIClient; print('Success!')"
```

### 8. Upload to PyPI

```bash
# Upload to production PyPI
python -m twine upload dist/*

# Verify upload
open https://pypi.org/project/smart-api-integrations/
```

## 🎯 Post-Release

### 1. Verify Installation

```bash
# Install from PyPI
pip install smart-api-integrations

# Test basic functionality
python -c "
from smart_api_integrations import UniversalAPIClient, GithubAPIClient
print('✅ Package installed successfully!')
print(f'Version: {smart_api_integrations.__version__}')
"

# Test CLI
smart-api-integrations --help
smart-api-integrations list-providers
```

### 2. Update Documentation

Update version references in:
- `README.md`
- `docs/quick-start-guide.md`
- Any version-specific documentation

### 3. Create GitHub Release

1. Go to [GitHub Releases](https://github.com/behera116/smart-api-integrations/releases)
2. Click "Create a new release"
3. **Tag**: `v0.1.1`
4. **Title**: `Smart API Integrations v0.1.1`
5. **Description**: Copy from CHANGELOG.md
6. **Attach files**: Upload `dist/` files
7. Click "Publish release"

## 🛠️ Automation Scripts

### Release Script

Create `scripts/release.py`:

```python
#!/usr/bin/env python3
"""
Release automation script for Smart API Integrations.
"""

import argparse
import subprocess
import sys
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command and return the result."""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    if result.returncode != 0:
        print(f"❌ Command failed: {cmd}")
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result.stdout.strip()

def update_version(version):
    """Update version in pyproject.toml and __init__.py"""
    # Update pyproject.toml
    pyproject_path = Path("pyproject.toml")
    content = pyproject_path.read_text()
    content = content.replace(
        'version = "0.1.0"',
        f'version = "{version}"'
    )
    pyproject_path.write_text(content)
    
    # Update __init__.py
    init_path = Path("src/__init__.py")
    content = init_path.read_text()
    content = content.replace(
        '__version__ = "0.1.0"',
        f'__version__ = "{version}"'
    )
    init_path.write_text(content)
    
    print(f"✅ Updated version to {version}")

def main():
    parser = argparse.ArgumentParser(description="Release Smart API Integrations")
    parser.add_argument("--version", required=True, help="Version to release (e.g., 0.1.1)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    
    args = parser.parse_args()
    
    if args.dry_run:
        print(f"🔍 Dry run: Would release version {args.version}")
        return
    
    # Update version
    update_version(args.version)
    
    # Run tests
    print("🧪 Running tests...")
    run_command("pytest")
    
    # Build package
    print("📦 Building package...")
    run_command("rm -rf dist/ build/ *.egg-info/")
    run_command("python -m build")
    
    # Commit and tag
    print("📝 Committing changes...")
    run_command(f"git add .")
    run_command(f"git commit -m 'Release v{args.version}'")
    run_command(f"git tag v{args.version}")
    
    print(f"✅ Release v{args.version} ready!")
    print("Next steps:")
    print(f"  1. git push origin main")
    print(f"  2. git push origin v{args.version}")
    print(f"  3. python -m twine upload dist/*")

if __name__ == "__main__":
    main()
```

### Pre-commit Hook

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-requests, types-PyYAML]
```

Install pre-commit hooks:

```bash
pip install pre-commit
pre-commit install
```

## 🔍 Troubleshooting

### Common Issues

**1. Upload fails with "File already exists"**
```bash
# Check if version already exists
pip index versions smart-api-integrations

# Increment version and try again
```

**2. Import errors after installation**
```bash
# Check package structure
python -c "import smart_api_integrations; print(smart_api_integrations.__file__)"

# Verify all dependencies are installed
pip show smart-api-integrations
```

**3. CLI not working**
```bash
# Check entry point
pip show smart-api-integrations | grep "Entry-points"

# Reinstall package
pip uninstall smart-api-integrations
pip install smart-api-integrations
```

**4. Authentication errors**
```bash
# Verify API token
echo $TWINE_PASSWORD

# Check ~/.pypirc configuration
cat ~/.pypirc
```

### Validation Commands

```bash
# Check package metadata
python -m twine check dist/*

# Verify wheel contents
python -m wheel unpack dist/smart_api_integrations-0.1.1-py3-none-any.whl
ls -la smart_api_integrations-0.1.1/

# Test import after installation
python -c "
import smart_api_integrations
from smart_api_integrations import UniversalAPIClient, GithubAPIClient
from smart_api_integrations.webhooks import smart_webhook_handler
print('✅ All imports successful')
"
```

## 📈 Release Checklist

- [ ] All tests pass (`pytest`)
- [ ] Code is formatted (`black`, `isort`)
- [ ] Type checking passes (`mypy`)
- [ ] Version updated in `pyproject.toml` and `src/__init__.py`
- [ ] `CHANGELOG.md` updated
- [ ] Changes committed and tagged
- [ ] Package built (`python -m build`)
- [ ] Package tested locally
- [ ] Uploaded to PyPI (`twine upload`)
- [ ] Installation verified from PyPI
- [ ] GitHub release created
- [ ] Documentation updated

## 🎉 Success!

Your package is now available on PyPI! Users can install it with:

```bash
pip install smart-api-integrations
```

And use it immediately:

```python
from smart_api_integrations import GithubAPIClient

github = GithubAPIClient()
user = github.get_user(username='octocat')
print(f"Hello, {user.data['name']}!")
``` 