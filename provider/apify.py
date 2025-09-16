from typing import Any
from apify_client import ApifyClient
from apify_client.errors import ApifyApiError
from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError
from http import HTTPStatus


def get_client(token: str) -> ApifyClient:
    return ApifyClient(token=token, timeout_secs=360)


class ApifyProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        token = (credentials.get("apify_token") or "").strip()
        if not token:
            msg = "Apify API Token is required."
            raise ToolProviderCredentialValidationError(msg)

        try:
            client = get_client(token)
            _ = client.user().get()
            return
        except ApifyApiError as e:
            code = getattr(e, "status_code", None)
            if code == HTTPStatus.UNAUTHORIZED:
                msg = "Invalid Apify API Token. Please check the token and try again."
                raise ToolProviderCredentialValidationError(msg) from e
            if code == HTTPStatus.FORBIDDEN:
                msg = "Apify API Token lacks required permissions (403 Forbidden)."
                raise ToolProviderCredentialValidationError(msg) from e

            msg = f"Apify API error while validating credentials: {e!s}"
            raise ToolProviderCredentialValidationError(msg) from e
        except Exception as e:
            msg = "Unable to reach Apify API. Please check network connectivity and try again."
            raise ToolProviderCredentialValidationError(msg) from e
