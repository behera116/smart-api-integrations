# OpenAPI Integration

Smart API Integrations now supports creating API clients directly from OpenAPI specifications. This feature allows you to leverage existing OpenAPI documentation to quickly create typed API clients with minimal effort.

## How It Works

The system can automatically generate API clients from:

1. Local OpenAPI specification files (YAML or JSON)
2. Remote OpenAPI specification URLs

The approach is to convert the OpenAPI specification to a config.yaml file once, and then use that file for all future client creation. This is efficient and avoids the overhead of parsing the OpenAPI spec on each client instantiation.

When you convert an OpenAPI specification to a config.yaml file:

1. The system extracts endpoints, parameters, and schemas
2. It creates a structured config.yaml file compatible with the Smart API Integrations system
3. The config.yaml file is stored in the provider directory for future use

The system then:
1. Uses the generated config.yaml file to create API clients
2. Creates a `ProviderConfig` with all the necessary information
3. Generates method stubs with proper typing and documentation
4. Provides both camelCase (original) and snake_case method names

## Using OpenAPI Clients

### Converting OpenAPI to config.yaml

You can convert an OpenAPI specification to a config.yaml file using the CLI tool:

```bash
# From the command line
smart-api-integrations openapi-to-config https://petstore3.swagger.io/api/v3/openapi.json --provider-name petstore

# Or with a local file
smart-api-integrations openapi-to-config path/to/openapi.yaml --provider-name my_api
```

Or programmatically:

```python
from smart_api_integrations.cli.openapi_converter import convert_openapi_to_config

# Convert from a URL
config_file = convert_openapi_to_config(
    "https://petstore3.swagger.io/api/v3/openapi.json",
    output_dir="path/to/output",
    provider_name="petstore"
)

# Or from a local file
config_file = convert_openapi_to_config(
    "path/to/openapi.yaml",
    output_dir="path/to/output",
    provider_name="my_api"
)
```

### Creating a Client

After converting the OpenAPI specification to a config.yaml file, creating a client is simple:

```python
from smart_api_integrations import UniversalAPIClient

# Create a client from either the config.yaml or OpenAPI specification
client = UniversalAPIClient("your_provider")

# List available methods
methods = client.list_available_methods()
print(methods)

# Get help for a specific method
help_text = client.get_method_help("get_user")
print(help_text)

# Call a method
response = client.get_user(user_id=123)
print(response.data)
```

### Method Naming

The system provides two ways to access API methods:

1. **Original operationId** (camelCase): `client.getPetById(petId=1)`
2. **Snake case version**: `client.get_pet_by_id(pet_id=1)`

Both formats will work, allowing you to choose the style that best fits your codebase.

## Loading from Remote URLs

You can also load OpenAPI specifications from remote URLs:

```python
from smart_api_integrations.core.loader import ConfigLoader

# Load from a remote URL
loader = ConfigLoader()
config = loader.load_remote_openapi_config(
    provider_name="petstore",
    openapi_url="https://petstore3.swagger.io/api/v3/openapi.json"
)

# Create a client using the loaded config
from smart_api_integrations import UniversalAPIClient
client = UniversalAPIClient("petstore")
```

## Enhanced Features

The OpenAPI integration provides several enhancements:

1. **Rich Documentation**: Method help includes parameter details, request body schemas, and example usage
2. **Parameter Validation**: Validates required parameters based on the OpenAPI specification
3. **Type Conversion**: Automatically handles parameter locations (path, query, body)
4. **Enum Support**: Validates enum parameters and provides documentation for allowed values
5. **Flexible Method Names**: Supports both camelCase and snake_case method names

## Examples

See the `examples/openapi_converter_example.py` file for a complete example of converting OpenAPI specifications to config.yaml files and using them with the UniversalAPIClient.

## Benefits of this Approach

Converting OpenAPI specifications to config.yaml files once and using those files for all future client creation has several advantages:

1. **Better Performance**: Avoids the overhead of parsing the OpenAPI spec on each client instantiation
2. **Simplified Dependencies**: The runtime dependencies are reduced since YAML/JSON parsing is only needed during conversion
3. **Customization**: The generated config.yaml file can be manually edited to customize behavior
4. **Version Control**: The config.yaml file can be version-controlled separately from the OpenAPI specification
5. **Consistency**: The config.yaml format ensures consistent behavior across all API clients 