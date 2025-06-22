# 📋 Sample Provider: GitHub

This repository includes GitHub as a **sample provider** to help you get started quickly.

## 🚀 Quick Test

```bash
# 1. Set your GitHub token
export GITHUB_TOKEN="your_github_token"

# 2. Test the sample provider
python examples/github_basic_example.py

# 3. Generate type stubs for IDE support
smart-api-integrations generate-type-stubs --provider github --output-dir "./typings"
```

## 📁 What's Included

- **`providers/github/config.yaml`** - Complete GitHub API configuration
- **`examples/github_basic_example.py`** - Working example with real API calls
- **`tests/test_github_provider.py`** - Test suite for the GitHub provider
- **`src/clients/github.py`** - Pre-built GitHub client class

## 🔧 Configuration Details

The GitHub provider demonstrates:
- ✅ Bearer token authentication
- ✅ 17 common GitHub API endpoints
- ✅ Path, query, and body parameters
- ✅ Proper error handling
- ✅ Type safety with generated stubs

## 🎯 Use as Template

You can use the GitHub provider configuration as a template for your own APIs:

1. Copy `providers/github/config.yaml` to `providers/yourapi/config.yaml`
2. Update the base URL, authentication, and endpoints
3. Generate your client: `smart-api-integrations generate-client yourapi`
4. Generate type stubs: `smart-api-integrations generate-type-stubs --provider yourapi`

## 🧪 Available Endpoints

The GitHub sample provider includes these endpoints:
- `get_authenticated_user()` - Get current user info
- `get_user(username)` - Get specific user
- `list_repos()` - List user repositories  
- `get_repo(owner, repo)` - Get specific repository
- `list_issues(owner, repo)` - List repository issues
- `create_issue(owner, repo, title)` - Create new issue
- And 11 more endpoints...

Run the tests to see all endpoints in action:
```bash
python -m pytest tests/test_github_provider.py -v
``` 