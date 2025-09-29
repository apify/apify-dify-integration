import secrets
from http import HTTPStatus
from typing import Any, Mapping
import time
from urllib.parse import urlencode

from apify_client.errors import ApifyApiError
from werkzeug import Request
import requests
from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError
from dify_plugin.entities.oauth import ToolOAuthCredentials
from dify_plugin.errors.tool import ToolProviderOAuthError

from tools.client import get_apify_client

APIFY_AUTHORIZATION_URL = "https://auth.apify.com/oauth/authorize"
APIFY_TOKEN_URL = "https://auth.apify.com/oauth/token"
APIFY_SCOPES = "user:read actor:run"


class ApifyProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        try:
            client = get_apify_client(credentials)
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

    def _oauth_get_authorization_url(self, redirect_uri: str, system_credentials: Mapping[str, Any]) -> str:
        """
        Generate the authorization URL for the user to start the OAuth flow.
        Corrected to match the ToolProvider interface.
        """
        state = secrets.token_urlsafe(16)

        client_id = system_credentials.get("client_id")
        if not client_id:
            raise ToolProviderOAuthError("OAuth client_id is not configured.")

        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": APIFY_SCOPES,
            "response_type": "code",
            "access_type": "offline",
            "state": state,
        }
        return f"{APIFY_AUTHORIZATION_URL}?{urlencode(params)}"

    def _oauth_get_credentials(
        self, redirect_uri: str, system_credentials: Mapping[str, Any], request: Request
    ) -> ToolOAuthCredentials:
        """
        Exchange the authorization code for an access token and refresh token.
        Corrected to match the ToolProvider interface.
        """

        client_id = system_credentials.get("client_id")
        client_secret = system_credentials.get("client_secret")

        if not client_id or not client_secret:
            raise ToolProviderOAuthError("OAuth client_id or client_secret is not configured.")

        code = request.args.get("code")

        if not code:
            raise ToolProviderOAuthError("Authorization code not provided")

        error = request.args.get("error")

        if error:
            error_description = request.args.get("error_description", "")
            raise ToolProviderOAuthError(f"OAuth authorization failed: {error} - {error_description}")

        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "client_secret": client_secret,
        }

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        try:
            response = requests.post(APIFY_TOKEN_URL, data=payload, headers=headers, timeout=10)
            response.raise_for_status()
            token_data = response.json()

            if "error" in token_data:
                error_desc = token_data.get("error_description", token_data["error"])
                raise ToolProviderOAuthError(f"Token exchange failed: {error_desc}")

            access_token = token_data.get("access_token")

            if not access_token:
                raise ToolProviderOAuthError("No access token received from provider")

            credentials = {
                "access_token": access_token,
                "token_type": token_data.get("token_type", "Bearer"),
            }

            refresh_token = token_data.get("refresh_token")

            if refresh_token:
                credentials["refresh_token"] = refresh_token

            expires_in = token_data.get("expires_in", 3600)
            expires_at = int(time.time()) + expires_in

            return ToolOAuthCredentials(credentials=credentials, expires_at=expires_at)

        except requests.RequestException as e:
            raise ToolProviderOAuthError(f"Network error during token exchange: {str(e)}")
        except Exception as e:
            raise ToolProviderOAuthError(f"Failed to exchange authorization code: {str(e)}")

    def _oauth_refresh_credentials(
        self, redirect_uri: str, system_credentials: Mapping[str, Any], credentials: Mapping[str, Any]
    ) -> ToolOAuthCredentials:
        """
        Use the refresh token to obtain a new access token.
        Corrected to match the ToolProvider interface.
        """

        refresh_token = credentials.get("refresh_token")
        if not refresh_token:
            raise ToolProviderOAuthError("No refresh token available")

        data = {
            "client_id": system_credentials["client_id"],
            "client_secret": system_credentials["client_secret"],
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        try:
            response = requests.post(APIFY_TOKEN_URL, data=data, headers=headers, timeout=10)
            response.raise_for_status()

            token_data = response.json()

            if "error" in token_data:
                error_desc = token_data.get("error_description", token_data["error"])
                raise ToolProviderOAuthError(f"Token refresh failed: {error_desc}")

            access_token = token_data.get("access_token")
            if not access_token:
                raise ToolProviderOAuthError("No access token received from provider")

            new_credentials = {
                "access_token": access_token,
                "token_type": token_data.get("token_type", "Bearer"),
                "refresh_token": refresh_token,  # Keep existing refresh token
            }

            expires_in = token_data.get("expires_in", 3600)

            new_refresh_token = token_data.get("refresh_token")
            if new_refresh_token:
                new_credentials["refresh_token"] = new_refresh_token

            expires_at = int(time.time()) + expires_in

            return ToolOAuthCredentials(credentials=new_credentials, expires_at=expires_at)

        except requests.RequestException as e:
            raise ToolProviderOAuthError(f"Network error during token refresh: {str(e)}")
        except Exception as e:
            raise ToolProviderOAuthError(f"Failed to refresh credentials: {str(e)}")
