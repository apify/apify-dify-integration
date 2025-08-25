import requests
from typing import Any
from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

class ApifyProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        """
        Validates the provided Apify API token by making a lightweight API call.
        """
        api_token = credentials.get('apify_token')
        if not api_token:
            raise ToolProviderCredentialValidationError("Apify API Token is required.")

        # This endpoint is a simple way to verify the token is valid
        validation_url = "https://api.apify.com/v2/users/me"
        headers = {
            "Authorization": f"Bearer {api_token}"
        }

        try:
            response = requests.get(validation_url, headers=headers, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            if hasattr(e, 'response') and e.response is not None and e.response.status_code == 401:
                raise ToolProviderCredentialValidationError(
                    "Invalid Apify API Token. Please check your token and try again."
                )
            else:
                raise ToolProviderCredentialValidationError(f"Failed to validate credentials: {str(e)}")