# 🎯 Provider Resolution Priority Guide

## ✅ **YES, Custom Providers OVERRIDE Built-in Providers**

When you set `SMART_API_INTEGRATIONS_PROVIDERS_DIR`, it completely overrides the built-in providers directory. Here's exactly how it works:

## 🔍 **Provider Resolution Logic**

The `ConfigLoader` resolves providers in this **strict priority order**:

1. **Explicit Directory Parameter** (highest priority)
   ```python
   loader = ConfigLoader(providers_directory="/path/to/custom")
   ```

2. **Environment Variable** (overrides built-in)
   ```bash
   export SMART_API_INTEGRATIONS_PROVIDERS_DIR="/path/to/custom"
   ```

3. **Built-in Package Providers** (fallback only)
   ```
   /site-packages/smart_api_integrations/providers/
   ```

## 🧪 **Tested Behavior**

### **Scenario 1: No Environment Variable**
```python
# Uses built-in GitHub provider
loader = ConfigLoader()
config = loader.load_provider_config('github')
print(config.base_url)  # → https://api.github.com
```

### **Scenario 2: With Environment Variable**
```bash
export SMART_API_INTEGRATIONS_PROVIDERS_DIR="./my_providers"
```
```python
# Uses custom GitHub provider (if exists)
loader = ConfigLoader()
config = loader.load_provider_config('github')
print(config.base_url)  # → https://custom-github-api.example.com/v1
```

## 🎯 **Key Points**

### ✅ **Complete Override**
- Environment variable **completely replaces** the built-in providers directory
- If you set `SMART_API_INTEGRATIONS_PROVIDERS_DIR`, the system **only** looks in that directory
- Built-in providers (like GitHub) are **not accessible** when environment variable is set

### ❌ **No Merging**
- The system does **NOT merge** custom and built-in providers
- It's an **either/or** situation, not both

## 🚀 **Practical Usage Patterns**

### **Pattern 1: Use Built-in Providers (Recommended for Quick Start)**
```python
# Don't set SMART_API_INTEGRATIONS_PROVIDERS_DIR
from smart_api_integrations import GithubAPIClient

github = GithubAPIClient()  # Uses built-in GitHub provider
```

### **Pattern 2: Override with Custom Providers**
```bash
# Create custom providers directory
mkdir -p ./my_providers/github
cp -r /path/to/builtin/github/* ./my_providers/github/

# Modify the custom config as needed
vim ./my_providers/github/config.yaml

# Set environment variable
export SMART_API_INTEGRATIONS_PROVIDERS_DIR="./my_providers"
```

### **Pattern 3: Mix Built-in and Custom**
If you want both built-in and custom providers, you need to copy built-in providers to your custom directory:

```bash
# Copy built-in providers to your custom directory
export SMART_API_INTEGRATIONS_PROVIDERS_DIR="./my_providers"

# Copy built-in GitHub provider
python -c "
import smart_api_integrations
from pathlib import Path
import shutil

# Find built-in providers
package_path = Path(smart_api_integrations.__file__).parent
builtin_providers = package_path / 'providers'

# Copy to custom directory
custom_providers = Path('./my_providers')
custom_providers.mkdir(exist_ok=True)

if (builtin_providers / 'github').exists():
    shutil.copytree(builtin_providers / 'github', custom_providers / 'github', dirs_exist_ok=True)
    print('✅ Copied built-in GitHub provider to custom directory')
"

# Now add your custom providers
mkdir -p ./my_providers/stripe
# ... create custom stripe config
```

## 🔧 **Configuration Examples**

### **Custom GitHub Provider Override**
```yaml
# ./my_providers/github/config.yaml
name: github
base_url: https://github.enterprise.com/api/v3  # Custom GitHub Enterprise
description: Custom GitHub Enterprise API
auth:
  type: bearer_token
  token_value: ${GITHUB_ENTERPRISE_TOKEN}        # Different token
endpoints:
  # Same endpoints as built-in, or add custom ones
  get_user:
    path: /users/{username}
    method: GET
    parameters:
      username: {type: string, required: true, in: path}
```

### **Environment Setup**
```bash
# Use custom providers directory
export SMART_API_INTEGRATIONS_PROVIDERS_DIR="./my_providers"

# Custom authentication
export GITHUB_ENTERPRISE_TOKEN="your_enterprise_token"
export STRIPE_API_KEY="sk_test_your_stripe_key"
```

## ⚠️ **Important Considerations**

1. **Complete Override**: Setting the environment variable means built-in providers are not accessible
2. **Provider Copying**: To use built-in providers alongside custom ones, copy them to your custom directory
3. **Authentication**: Custom providers can use different authentication methods and environment variables
4. **Maintenance**: You're responsible for maintaining custom provider configurations

## 🎉 **Summary**

- **✅ Custom providers completely override built-in providers**
- **✅ Environment variable has higher priority than built-in directory**
- **✅ No automatic merging - it's either custom OR built-in**
- **✅ You can copy built-in providers to custom directory if needed**

This gives you complete control over provider configurations while maintaining the convenience of built-in providers when you don't need customization. 