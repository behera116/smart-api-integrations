# Framework Integrations

This directory contains integrations for popular web frameworks to make it easy to use the Smart API Integrations webhook system.

## Available Integrations

- **Flask**: `flask.py` - Integration for Flask web framework
- **Django**: `django.py` - Integration for Django web framework
- **FastAPI**: `fastapi.py` - Integration for FastAPI web framework

## How to Use

### Flask

```python
from flask import Flask
from smart_api_integrations.frameworks.flask import register_webhook_routes

# Import your webhook handlers
import webhook_handlers

app = Flask(__name__)

# Register webhook routes
register_webhook_routes(app)

if __name__ == '__main__':
    app.run(debug=True)
```

### Django

```python
# urls.py
from django.urls import path
from smart_api_integrations.frameworks.django import webhook_view

# Import your webhook handlers
import webhook_handlers

urlpatterns = [
    # This will create endpoints for all registered webhooks
    path('webhooks/<str:provider>/', webhook_view, name='webhook'),
    path('webhooks/<str:provider>/<str:webhook_name>/', webhook_view, name='webhook_named'),
]
```

### FastAPI

```python
from fastapi import FastAPI
from smart_api_integrations.frameworks.fastapi import register_webhook_routes

# Import your webhook handlers
import webhook_handlers

app = FastAPI()

# Register webhook routes
register_webhook_routes(app)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## How It Works

Each framework integration provides:

1. A way to register webhook routes with the framework
2. A view function to handle incoming webhook requests
3. Integration with the Smart API Integrations webhook system

When a webhook request is received:

1. The framework integration verifies the webhook signature
2. It parses the webhook payload into a standardized format
3. It routes the event to the appropriate handler
4. It returns a standardized response

## Adding New Framework Integrations

To add a new framework integration:

1. Create a new file in this directory (e.g., `pyramid.py`)
2. Implement a function to register webhook routes with the framework
3. Implement a view function to handle incoming webhook requests
4. Update the `__init__.py` file to expose the new integration

See the existing integrations for examples of how to implement these functions. 