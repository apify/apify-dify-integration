from apify_client import ApifyClient
from typing import Any

from dify_plugin.entities.tool import ToolRuntime

TRACKING_HEADER = {"x-apify-integration-platform": "dify"}


def get_apify_client(credentials: dict[str, Any] | ToolRuntime) -> ApifyClient:
    """
    Initializes and returns a configured ApifyClient instance with a custom header.
    It temporarily patches the underlying HTTP client to inject the header during creation.
    """    
    creds_dict = {}

    if isinstance(credentials, ToolRuntime):
        creds_dict = credentials.credentials
    elif isinstance(credentials, dict):
        creds_dict = credentials
    
    token = None
    if "access_token" in creds_dict:
        token = creds_dict["access_token"]
    elif "apify_token" in creds_dict:
        token = creds_dict["apify_token"]
    else:
        raise ValueError("Expected credentials to have 'access_token' or 'apify_token' key.")

    if not token:
        raise ValueError("Apify authentication token not found. Please authorize the plugin or configure an API Token.")

    client = ApifyClient(token)
    original_prepare_request_call = client.http_client._prepare_request_call

    def wrapped_prepare_request_call(*args: Any, **kwargs: Any) -> tuple:
        headers, parsed_params, data = original_prepare_request_call(*args, **kwargs)
        headers.update(TRACKING_HEADER)

        return headers, parsed_params, data

    client.http_client._prepare_request_call = wrapped_prepare_request_call

    return client
