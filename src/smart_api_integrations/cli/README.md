# Smart API Integrations CLI

Command-line interface for the Smart API Integrations framework.

## Installation

```bash
pip install smart_api_integrations
```

## Usage

```bash
smart-api-integrations --help
```

## Available Commands

### Add Provider

Create a new API provider configuration:

```bash
smart-api-integrations add-provider --name github --base-url "https://api.github.com" --auth bearer
smart-api-integrations add-provider --interactive
```

### Add Endpoints

Add endpoints to an existing provider using AI:

```bash
smart-api-integrations add-endpoints --provider github --url "https://docs.github.com/en/rest/users"
```

### Test Webhook

Test webhook handlers with sample payloads:

```bash
smart-api-integrations test-webhook github push
smart-api-integrations test-webhook stripe payment_intent.succeeded --payload-file ./payload.json
```

### Generate Type Stubs

Generate type stub files for better IDE support:

```bash
smart-api-integrations generate-type-stubs
smart-api-integrations generate-type-stubs --provider github
```

### Test API

Test the Smart API system:

```bash
smart-api-integrations test
smart-api-integrations test --provider github
smart-api-integrations test --list-providers
```

## Environment Variables

- `SMART_API_INTEGRATIONS_PROVIDERS_DIR`: Directory containing provider configurations (default: `./providers`)
- `OPENAI_API_KEY`: OpenAI API key for AI-powered features 