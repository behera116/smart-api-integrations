# 🛠️ CLI Reference

## 🎯 Overview

The Smart API Integrations CLI provides powerful commands for managing providers, generating code, and testing integrations. All commands follow the pattern `smart-api-integrations <command> [options]`.

## 📦 Installation

```bash
pip install smart-api-integrations
```

## 🔧 Global Options

| Option | Description | Default |
|--------|-------------|---------|
| `--providers-dir` | Directory containing provider configurations | `./providers` |
| `--help` | Show help for any command | - |
| `--version` | Show version information | - |

## 🔌 Provider Management

### `add-provider`
Create a new API provider configuration.

```bash
smart-api-integrations add-provider \
    --name "myapi" \
    --base-url "https://api.myservice.com/v1" \
    --auth-type "bearer_token" \
    --description "My API Service"
```

**Options:**
- `--name` (required): Provider name
- `--base-url` (required): Base API URL
- `--auth-type`: Authentication type (`bearer_token`, `api_key`, `basic`, `oauth2`, `jwt`)
- `--description`: Provider description
- `--output-dir`: Output directory (default: `./providers/{name}`)

**Example:**
```bash
# Create Stripe provider
smart-api-integrations add-provider \
    --name "stripe" \
    --base-url "https://api.stripe.com/v1" \
    --auth-type "bearer_token" \
    --description "Stripe Payment Processing API"
```

### `list-providers`
List all configured providers.

```bash
smart-api-integrations list-providers
```

**Options:**
- `--format`: Output format (`table`, `json`, `yaml`)
- `--show-endpoints`: Include endpoint counts

**Example Output:**
```
Provider    Base URL                     Auth Type      Endpoints
github      https://api.github.com       bearer_token   12
stripe      https://api.stripe.com/v1    bearer_token   8
myapi       https://api.myservice.com/v1 bearer_token   5
```

### `add-endpoints`
Add endpoints to an existing provider using AI generation.

```bash
smart-api-integrations add-endpoints myapi \
    --url "https://docs.myservice.com/api" \
    --max-endpoints 10 \
    --model "gpt-4"
```

**Options:**
- `provider` (required): Provider name
- `--url`: Documentation URL for AI analysis
- `--max-endpoints`: Maximum endpoints to generate (default: 20)
- `--model`: AI model to use (`gpt-4`, `gpt-3.5-turbo`)
- `--output-format`: Output format (`yaml`, `json`)
- `--dry-run`: Show what would be generated without saving

## 🏗️ Code Generation

### `generate-client`
Generate a dedicated client class for a provider.

```bash
smart-api-integrations generate-client myapi \
    --class-name "MyAPIClient" \
    --output-file "./clients/myapi_client.py"
```

**Options:**
- `provider` (required): Provider name
- `--class-name`: Client class name (default: `{Provider}APIClient`)
- `--output-file`: Output file path
- `--template`: Template to use (`standard`, `minimal`, `advanced`)
- `--include-docs`: Include docstrings and examples

**Generated Client Example:**
```python
# clients/myapi_client.py
import os
from smart_api_integrations import UniversalAPIClient

class MyAPIClient(UniversalAPIClient):
    def __init__(self, **auth_overrides):
        if 'token_value' not in auth_overrides:
            token = os.getenv('MYAPI_TOKEN')
            if token:
                auth_overrides['token_value'] = token
        super().__init__('myapi', **auth_overrides)
```

### `generate-type-stubs`
Generate type stubs for full IDE support.

```bash
smart-api-integrations generate-type-stubs myapi \
    --output-dir "./typings"
```

**Options:**
- `provider` (required): Provider name
- `--output-dir`: Output directory (default: `./typings`)
- `--format`: Stub format (`pyi`, `py`)
- `--include-examples`: Include usage examples in stubs

**Generated Stub Example:**
```python
# typings/myapi.pyi
from smart_api_integrations.core.schema import APIResponse

class MyAPIClient:
    def get_user(self, user_id: str) -> APIResponse: ...
    def list_users(self, page: int = None, limit: int = None) -> APIResponse: ...
    def create_user(self, name: str, email: str) -> APIResponse: ...
```

## 🪝 Webhook Management

### `add-webhook`
Add webhook configuration to a provider.

```bash
smart-api-integrations add-webhook github \
    --event push \
    --secret-env GITHUB_WEBHOOK_SECRET
```

**Options:**
- `provider` (required): Provider name
- `--event`: Webhook event type (can be used multiple times)
- `--secret-env`: Environment variable for webhook secret
- `--path`: Webhook endpoint path (default: `/webhooks/{provider}`)
- `--verification-type`: Signature verification type (`hmac_sha256`, `hmac_sha1`, `jwt`)
- `--signature-header`: Header containing signature
- `--event-header`: Header containing event type

**Example:**
```bash
# Add multiple events
smart-api-integrations add-webhook stripe \
    --event payment_intent.succeeded \
    --event customer.created \
    --secret-env STRIPE_WEBHOOK_SECRET \
    --verification-type hmac_sha256
```

### `generate-webhook-handler`
Generate webhook handler class for a provider.

```bash
smart-api-integrations generate-webhook-handler github \
    --events push pull_request \
    --output-file "./handlers/github_handler.py"
```

**Options:**
- `provider` (required): Provider name
- `--events`: Event types to handle (space-separated)
- `--output-file`: Output file path
- `--class-name`: Handler class name (default: `{Provider}Handler`)
- `--template`: Template to use (`standard`, `minimal`, `advanced`)
- `--include-examples`: Include example implementations

### `test-webhook`
Test webhook handlers with sample payloads.

```bash
smart-api-integrations test-webhook github push
```

**Options:**
- `provider` (required): Provider name
- `event` (required): Event type to test
- `--payload-file`: Custom payload file
- `--handler-file`: Handler file to test
- `--verbose`: Show detailed output

**Example:**
```bash
# Test with custom payload
smart-api-integrations test-webhook stripe payment_intent.succeeded \
    --payload-file ./test_data/stripe_payment.json \
    --verbose
```

## 🧪 Testing & Validation

### `test`
Test provider configuration and endpoints.

```bash
smart-api-integrations test myapi --endpoint get_user
```

**Options:**
- `provider` (required): Provider name
- `--endpoint`: Specific endpoint to test
- `--dry-run`: Validate configuration without making API calls
- `--auth-test`: Test authentication only
- `--verbose`: Show detailed output

### `validate`
Validate provider configurations.

```bash
smart-api-integrations validate
```

**Options:**
- `--provider`: Specific provider to validate
- `--strict`: Enable strict validation
- `--fix`: Attempt to fix common issues

**Example Output:**
```
✅ github: Configuration valid (12 endpoints)
❌ myapi: Missing required field 'base_url'
⚠️  stripe: Deprecated auth format detected
```

## 📊 Information & Debugging

### `info`
Show detailed information about a provider.

```bash
smart-api-integrations info github
```

**Options:**
- `provider` (required): Provider name
- `--format`: Output format (`table`, `json`, `yaml`)
- `--show-endpoints`: Include endpoint details
- `--show-config`: Include full configuration

### `debug`
Debug provider issues and configurations.

```bash
smart-api-integrations debug myapi
```

**Options:**
- `provider` (required): Provider name
- `--check-auth`: Test authentication
- `--check-endpoints`: Validate all endpoints
- `--verbose`: Show detailed debug information

## 🔧 Configuration Management

### `config`
Manage global configuration settings.

```bash
# Show current configuration
smart-api-integrations config show

# Set configuration value
smart-api-integrations config set providers_dir ./my-providers

# Reset to defaults
smart-api-integrations config reset
```

**Available Settings:**
- `providers_dir`: Default providers directory
- `default_auth_type`: Default authentication type
- `ai_model`: Default AI model for endpoint generation
- `output_format`: Default output format

## 📁 File Operations

### `export`
Export provider configurations.

```bash
smart-api-integrations export --provider github --output github-config.yaml
```

**Options:**
- `--provider`: Specific provider to export
- `--output`: Output file path
- `--format`: Export format (`yaml`, `json`)
- `--include-secrets`: Include secret values (use with caution)

### `import`
Import provider configurations.

```bash
smart-api-integrations import --file github-config.yaml
```

**Options:**
- `--file` (required): Configuration file to import
- `--overwrite`: Overwrite existing providers
- `--dry-run`: Show what would be imported

## 🎯 Real-World Examples

### Complete Provider Setup
```bash
# 1. Create provider
smart-api-integrations add-provider \
    --name "shopify" \
    --base-url "https://{shop}.myshopify.com/admin/api/2023-04" \
    --auth-type "bearer_token"

# 2. Generate endpoints from docs
smart-api-integrations add-endpoints shopify \
    --url "https://shopify.dev/docs/api/admin-rest" \
    --max-endpoints 15

# 3. Generate client class
smart-api-integrations generate-client shopify \
    --output-file "./clients/shopify_client.py"

# 4. Generate type stubs
smart-api-integrations generate-type-stubs shopify

# 5. Add webhook support
smart-api-integrations add-webhook shopify \
    --event orders/create \
    --event orders/updated \
    --secret-env SHOPIFY_WEBHOOK_SECRET

# 6. Generate webhook handler
smart-api-integrations generate-webhook-handler shopify \
    --events orders/create orders/updated \
    --output-file "./handlers/shopify_handler.py"

# 7. Test everything
smart-api-integrations test shopify --verbose
```

### Development Workflow
```bash
# Validate all configurations
smart-api-integrations validate

# List all providers with details
smart-api-integrations list-providers --show-endpoints

# Test specific provider
smart-api-integrations test myapi --endpoint get_user --verbose

# Debug authentication issues
smart-api-integrations debug myapi --check-auth

# Export configuration for backup
smart-api-integrations export --output backup-$(date +%Y%m%d).yaml
```

## 🆘 Help & Troubleshooting

### Getting Help
```bash
# General help
smart-api-integrations --help

# Command-specific help
smart-api-integrations add-provider --help
smart-api-integrations generate-client --help
```

### Common Issues

**Provider not found:**
```bash
# Check providers directory
smart-api-integrations config show
smart-api-integrations list-providers
```

**Authentication errors:**
```bash
# Debug authentication
smart-api-integrations debug myapi --check-auth --verbose
```

**Configuration errors:**
```bash
# Validate and fix
smart-api-integrations validate --provider myapi --fix
```

## 🚀 Next Steps

- **[Quick Start Guide](quick-start-guide.md)** - Get started in 5 minutes
- **[Adding New Providers](adding-new-providers.md)** - Detailed provider setup
- **[Webhook Handler Guide](webhook-handler-guide.md)** - Webhook implementation
- **[Best Practices](best-practices.md)** - Production deployment tips 