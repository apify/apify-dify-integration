from apify_client import ApifyClient
from typing import Any

from dify_plugin.entities.tool import CredentialType

TRACKING_HEADER = {"x-apify-integration-platform": "dify"}


def get_apify_client(credentials: dict[str, Any], credential_type: CredentialType) -> ApifyClient:
    """
    Initializes and returns a configured ApifyClient instance with a custom header.
    It temporarily patches the underlying HTTP client to inject the header during creation.

    Args:
        credentials: Credentials dict containing the authentication token
        credential_type: Type of credentials (OAUTH or API_KEY)
    """

    # Extract token based on credential type
    if credential_type == CredentialType.OAUTH:
        token = credentials.get("access_token")
        if not token:
            raise ValueError("OAuth access_token not found in credentials")
    elif credential_type == CredentialType.API_KEY:
        token = credentials.get("apify_token")
        if not token:
            raise ValueError("API key (apify_token) not found in credentials")
    else:
        raise ValueError(f"Unsupported credential type: {credential_type}")

    client = ApifyClient(token)
    original_prepare_request_call = client.http_client._prepare_request_call

    def wrapped_prepare_request_call(*args: Any, **kwargs: Any) -> tuple:
        headers, parsed_params, data = original_prepare_request_call(*args, **kwargs)
        headers.update(TRACKING_HEADER)

        return headers, parsed_params, data

    client.http_client._prepare_request_call = wrapped_prepare_request_call

    return client
