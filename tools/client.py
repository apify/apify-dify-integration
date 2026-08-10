from apify_client import ApifyClient
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from dify_plugin.entities.tool import CredentialType

TRACKING_HEADER = {"x-apify-integration-platform": "dify"}


def get_apify_client(credentials: dict[str, Any], credential_type: CredentialType) -> ApifyClient:
    """
    Initializes and returns a configured ApifyClient instance with a custom tracking header.

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

    return ApifyClient(token, headers=TRACKING_HEADER)


def run_to_dict(run: Any) -> dict[str, Any]:
    """
    Serializes an apify-client v3 `Run` model into the plain dict Dify expects.

    The model cannot be yielded as-is because Dify fails to serialize it, and `by_alias` keeps
    the output keys camelCase (`defaultDatasetId`, ...) for downstream workflow nodes.
    """
    payload = run.model_dump(by_alias=True, mode="json")

    # Pydantic normalises `containerUrl` with a trailing "/" that the Apify API does not send;
    # strips it so the value stays safe to concatenate onto.
    container_url = payload.get("containerUrl")
    if isinstance(container_url, str):
        parts = urlsplit(container_url)
        if parts.path == "/":
            payload["containerUrl"] = urlunsplit(parts._replace(path=""))

    return payload
