# 🚀 Quick Start Guide

Get up and running with Smart API Integrations in 5 minutes!

## 📦 1. Installation

```bash
pip install smart-api-integrations
```

## 🔧 2. Environment Setup

```bash
# Set your providers directory
export SMART_API_INTEGRATIONS_PROVIDERS_DIR="./providers"

# Set authentication tokens (provider-specific)
export GITHUB_TOKEN="your_github_token"
export STRIPE_API_KEY="your_stripe_key"
```

## 🎯 3. Use Pre-built Providers

GitHub comes pre-configured as an example:

```python
from smart_api_integrations import GithubAPIClient

# Uses GITHUB_TOKEN automatically
github = GithubAPIClient()
user = github.get_user(username='octocat')
print(f"User: {user.data['name']}")
```

## 🔌 4. Add Your Own Provider

### Option A: Manual Configuration
```bash
mkdir -p providers/myapi
cat > providers/myapi/config.yaml << 'EOF'
name: myapi
base_url: https://api.myservice.com/v1
auth:
  type: bearer_token
  token_value: ${MYAPI_TOKEN}
endpoints:
  get_user:
    path: /users/{user_id}
    method: GET
    parameters:
      user_id: {type: string, required: true, in: path}
EOF
```

### Option B: CLI Generation
```bash
smart-api-integrations add-provider \
    --name "myapi" \
    --base-url "https://api.myservice.com/v1" \
    --auth-type "bearer_token"
```

## 💻 5. Use Your Provider

```python
from smart_api_integrations import UniversalAPIClient

# Set your token
import os
os.environ['MYAPI_TOKEN'] = 'your_token'

# Use the client
api = UniversalAPIClient('myapi')
user = api.get_user(user_id='123')
print(f"User: {user.data}")
```

## 🪝 6. Add Webhooks (Optional)

```bash
# Add webhook configuration
smart-api-integrations add-webhook myapi --event user.created

# Generate handler
smart-api-integrations generate-webhook-handler myapi \
    --events user.created \
    --output-file ./handlers/myapi_handler.py
```

```python
# Use the handler
from handlers.myapi_handler import MyAPIHandler
from flask import Flask
from smart_api_integrations.frameworks.flask import get_webhook_routes

app = Flask(__name__)
app.register_blueprint(get_webhook_routes('flask', {
    'myapi': MyAPIHandler()
}))
```

## ✅ You're Done!

You now have:
- ✅ Intelligent API client with zero boilerplate
- ✅ Automatic parameter routing (path/query/body)
- ✅ Environment-based authentication
- ✅ Optional webhook handling
- ✅ Framework integration ready

## 🎯 Next Steps

- **[Generate type stubs](type-safety-guide.md)** for full IDE support
- **[Add more providers](adding-new-providers.md)** for your APIs
- **[Explore examples](examples/README.md)** for real-world usage
- **[Learn about webhooks](webhook-system-overview.md)** for event handling

## 💡 Pro Tips

1. **Use environment variables** for all authentication tokens
2. **Generate type stubs** for better IDE experience
3. **Check the examples/** directory for real-world patterns
4. **Use the CLI** for quick provider setup

```bash
# Generate everything at once
smart-api-integrations generate-client myapi --output-file ./clients/myapi.py
smart-api-integrations generate-type-stubs myapi --output-dir ./typings
``` 