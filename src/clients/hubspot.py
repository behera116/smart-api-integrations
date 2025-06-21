"""
HubSpot API Client - Simple alias for method-based access.
"""

import os
from .universal import UniversalAPIClient


class HubspotAPIClient(UniversalAPIClient):
    """
    HubSpot API Client.
    
    Usage:
        hubspot = HubspotAPIClient()  # Gets token from HUBSPOT_TOKEN env var
        contacts = hubspot.list_contacts(params={'limit': 10})
        contact = hubspot.create_contact(json_data={'properties': {...}})
    """
    
    # Optional method mapping for more Pythonic names
    METHOD_MAPPING = {
        'list_contacts': 'listcontacts',
        'create_contact': 'createcontact',
        'get_contact': 'getcontact',
        'update_contact': 'updatecontact',
        'delete_contact': 'deletecontact',
        'list_companies': 'listcompanies',
        'create_company': 'createcompany',
    }
    
    def __init__(self, token_value: str = None):
        """
        Initialize HubSpot API client.
        
        Args:
            token_value: HubSpot token (optional, defaults to HUBSPOT_TOKEN env var)
        """
        token = token_value or os.getenv('HUBSPOT_TOKEN')
        if not token:
            raise ValueError("HubSpot token required. Set HUBSPOT_TOKEN environment variable or pass token_value.")
        
        super().__init__('hubspot', token_value=token) 