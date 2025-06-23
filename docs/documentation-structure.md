# Documentation Structure

This document provides an overview of the Smart API Integrations documentation structure and how to navigate it.

## Documentation Organization

The documentation is organized into the following sections:

### 1. Getting Started
- [Quick Start Guide](quick-start-guide.md) - Basic introduction to the library
- [API Client Guide](api-client-guide.md) - How to use API clients
- [Webhook Integration](webhook_integration.md) - How to use webhook handlers

### 2. API Integration
- [Adding New Providers](adding-new-providers.md) - How to add new API providers
- [OpenAPI Integration](openapi_integration.md) - How to use OpenAPI specifications
- [Type Safety Guide](type-safety-guide.md) - How to use type hints and stubs

### 3. Webhook Integration
- [Webhook System Overview](webhook-system-overview.md) - How the webhook system works
- [Webhook Handler Guide](webhook-handler-guide.md) - How to create webhook handlers
- [Framework Integration Guide](framework-integration-guide.md) - How to integrate with web frameworks

### 4. Reference
- [CLI Reference](cli-reference.md) - Command-line tool reference
- [Provider Configuration Guide](provider-priority-guide.md) - How to configure providers
- [Package Setup Guide](package-setup-guide.md) - How to set up the package

## Examples

The `examples/` directory contains working examples of how to use the library:

- [API Examples](../examples/github_basic_example.py) - Basic API client usage
- [Webhook Examples](../examples/webhook_integration_example.py) - Webhook handler examples
- [Framework Examples](../examples/flask_webhook_example.py) - Framework integration examples

## Navigation Tips

1. **Start with the README**: The main README.md file provides a concise overview and "before vs after" examples.
2. **Follow the Quick Start Guide**: For a step-by-step introduction to the library.
3. **Check the Examples**: For working code that you can run and modify.
4. **Dive into Specific Guides**: Once you understand the basics, explore the specific guides for your use case.

## Contributing to Documentation

If you find errors or want to improve the documentation:

1. Create a new branch
2. Make your changes
3. Submit a pull request

We welcome contributions to make the documentation more clear and helpful! 