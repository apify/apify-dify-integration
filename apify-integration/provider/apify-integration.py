from typing import Any
import requests

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

class ApifyProvider(ToolProvider):
    
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        """
        This function is called when the user saves their credentials in the Dify UI.
        It makes a test API call to Apify to verify the token is valid.
        """
        token = credentials.get('apify_token')

        if not token:
            raise ToolProviderCredentialValidationError("Apify API Token is required.")

        validation_url = f"https://api.apify.com/v2/users/me?token={token}"
        
        try:
            response = requests.get(validation_url)

            if response.status_code == 401:
                raise ToolProviderCredentialValidationError("Invalid Apify API Token.")
            
            response.raise_for_status()

        except requests.exceptions.RequestException as e:
            raise ToolProviderCredentialValidationError(f"Failed to connect to Apify to validate the token: {e}")
        except Exception as e:
            raise ToolProviderCredentialValidationError(f"An unexpected error occurred during validation: {e}")