"""
Authentication resolvers for Smart API system.
Supports API Key, OAuth2, JWT, Basic auth, and Bearer tokens.
Synchronous implementation for simplicity.
"""

import base64
import time
import hashlib
from typing import Dict, Optional

import httpx
from .schema import AuthConfig, AuthType, TokenCache


class AuthResolver:
    """Base class for authentication resolvers."""
    
    def __init__(self, config: AuthConfig):
        self.config = config
        self._token_cache: Dict[str, TokenCache] = {}
    
    def apply_auth(self, request: httpx.Request) -> httpx.Request:
        """Apply authentication to the request."""
        return request
    
    def get_cache_key(self) -> str:
        """Generate a cache key for token storage."""
        if self.config.token_cache_key:
            return self.config.token_cache_key
        
        # Generate based on auth config
        key_components = [
            self.config.type.value,
            self.config.oauth2_client_id or "",
            self.config.username or ""
        ]
        return hashlib.md5("|".join(key_components).encode()).hexdigest()


class NoAuthResolver(AuthResolver):
    """No authentication resolver."""
    pass


class APIKeyResolver(AuthResolver):
    """API Key authentication resolver."""
    
    def apply_auth(self, request: httpx.Request) -> httpx.Request:
        if self.config.api_key_header:
            request.headers[self.config.api_key_header] = self.config.api_key_value
        
        if self.config.api_key_param:
            # Add to query parameters
            if request.url.params:
                params = dict(request.url.params)
            else:
                params = {}
            params[self.config.api_key_param] = self.config.api_key_value
            request.url = request.url.copy_with(params=params)
        
        return request


class BearerTokenResolver(AuthResolver):
    """Bearer token authentication resolver."""
    
    def apply_auth(self, request: httpx.Request) -> httpx.Request:
        request.headers["Authorization"] = f"Bearer {self.config.token_value}"
        return request


class BasicAuthResolver(AuthResolver):
    """Basic authentication resolver."""
    
    def apply_auth(self, request: httpx.Request) -> httpx.Request:
        credentials = f"{self.config.username}:{self.config.password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        request.headers["Authorization"] = f"Basic {encoded_credentials}"
        return request


class JWTResolver(AuthResolver):
    """JWT authentication resolver."""
    
    def apply_auth(self, request: httpx.Request) -> httpx.Request:
        request.headers["Authorization"] = f"Bearer {self.config.jwt_token}"
        return request


class OAuth2Resolver(AuthResolver):
    """OAuth2 authentication resolver with token caching."""
    
    def apply_auth(self, request: httpx.Request) -> httpx.Request:
        token = self._get_valid_token()
        if token:
            request.headers["Authorization"] = f"{token.token_type} {token.access_token}"
        return request
    
    def _get_valid_token(self) -> Optional[TokenCache]:
        """Get a valid OAuth2 token, refreshing if necessary."""
        cache_key = self.get_cache_key()
        
        # Check cache if enabled
        if self.config.cache_tokens and cache_key in self._token_cache:
            cached_token = self._token_cache[cache_key]
            if not cached_token.is_expired():
                return cached_token
        
        # Request new token
        token = self._request_new_token()
        
        # Cache if enabled
        if self.config.cache_tokens and token:
            self._token_cache[cache_key] = token
        
        return token
    
    def _request_new_token(self) -> Optional[TokenCache]:
        """Request a new OAuth2 token."""
        if not all([self.config.oauth2_client_id, self.config.oauth2_client_secret, self.config.oauth2_token_url]):
            raise ValueError("OAuth2 configuration incomplete")
        
        data = {
            "grant_type": "client_credentials",
            "client_id": self.config.oauth2_client_id,
            "client_secret": self.config.oauth2_client_secret,
        }
        
        if self.config.oauth2_scopes:
            data["scope"] = " ".join(self.config.oauth2_scopes)
        
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        with httpx.Client() as client:
            try:
                response = client.post(
                    self.config.oauth2_token_url,
                    data=data,
                    headers=headers,
                    timeout=30.0
                )
                response.raise_for_status()
                
                token_data = response.json()
                return TokenCache(
                    access_token=token_data.get("access_token"),
                    token_type=token_data.get("token_type", "Bearer"),
                    expires_in=token_data.get("expires_in"),
                    refresh_token=token_data.get("refresh_token"),
                    scope=token_data.get("scope"),
                    created_at=time.time()
                )
            except httpx.HTTPError as e:
                print(f"OAuth2 token request failed: {e}")
                return None


class AuthResolverFactory:
    """Factory for creating authentication resolvers."""
    
    _resolvers = {
        AuthType.NONE: NoAuthResolver,
        AuthType.API_KEY: APIKeyResolver,
        AuthType.BEARER_TOKEN: BearerTokenResolver,
        AuthType.BASIC: BasicAuthResolver,
        AuthType.JWT: JWTResolver,
        AuthType.OAUTH2: OAuth2Resolver,
    }
    
    @classmethod
    def create_resolver(cls, config: AuthConfig) -> AuthResolver:
        """Create an authentication resolver based on the config."""
        resolver_class = cls._resolvers.get(config.type)
        if not resolver_class:
            raise ValueError(f"Unsupported authentication type: {config.type}")
        
        return resolver_class(config)
    
    @classmethod
    def register_resolver(cls, auth_type: AuthType, resolver_class: type):
        """Register a custom authentication resolver."""
        cls._resolvers[auth_type] = resolver_class
