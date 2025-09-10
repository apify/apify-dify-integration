from apify_client import ApifyClient
from typing import Any

TRACKING_HEADER = {"x-apify-integration-platform": "dify"}


def get_apify_client(api_token: str) -> ApifyClient:
    """
    Initializes and returns a configured ApifyClient instance with a custom header.
    It temporarily patches the underlying HTTP client to inject the header during creation.
    """
    if not api_token:
        raise ValueError("Error: Apify API Token not found in credentials.")

    client = ApifyClient(token=api_token)
    original_prepare_request_call = client.http_client._prepare_request_call

    def wrapped_prepare_request_call(*args: Any, **kwargs: Any) -> tuple:
        headers, parsed_params, data = original_prepare_request_call(*args, **kwargs)
        headers.update(TRACKING_HEADER)

        return headers, parsed_params, data

    client.http_client._prepare_request_call = wrapped_prepare_request_call

    return client
