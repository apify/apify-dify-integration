import time
from collections.abc import Generator
from typing import Any

import requests
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools.client import TRACKING_HEADER, get_apify_token
from utils.error_handling import (
    PASSTHROUGH_ERRORS,
    ToolInvokeError,
    ToolParameterValidationError,
    parse_json_param,
    raise_apify_response_error,
    raise_unexpected_error,
    require_param,
    validate_url,
)

# Standby endpoint of the apify/web-fetch Actor. It responds with the fetched page in a single request.
WEB_FETCH_STANDBY_URL = "https://web-fetch.apify.actor/"
WEB_FETCH_FORMATS = ("markdown", "html", "text", "links", "raw")
CONNECT_TIMEOUT_SECS = 10
# Dify may cut a plugin request off at 120s (MAX_REQUEST_TIMEOUT in main.py), which is shorter than Web Fetch's own
# 2-minute limit, so the tool stops waiting a bit earlier to report a clear timeout instead of a generic one.
TOTAL_TIMEOUT_SECS = 110
# Retries apply only to errors of the Apify platform in front of the Actor (5xx, 429). Web Fetch errors are final,
# because the Actor already retries the fetch of the target URL internally.
MAX_RETRIES = 3
RETRY_BACKOFF_SECS = 0.2
ACTION = "fetching URL"


def parse_formats(raw_formats: Any) -> list[str]:
    """
    Parses the comma-separated `formats` parameter (a list is accepted too) into a deduplicated list of Web Fetch
    formats. An empty list means Web Fetch picks the format based on the content type.
    """
    if raw_formats is None:
        return []
    if isinstance(raw_formats, str):
        items = raw_formats.split(",")
    elif isinstance(raw_formats, list):
        items = raw_formats
    else:
        raise ToolParameterValidationError("formats must be a comma-separated string, e.g. 'markdown,links'.")

    formats: list[str] = []
    for item in items:
        if not isinstance(item, str):
            raise ToolParameterValidationError("formats must be a comma-separated string, e.g. 'markdown,links'.")
        value = item.strip().lower()
        if not value:
            continue
        if value not in WEB_FETCH_FORMATS:
            raise ToolParameterValidationError(
                f"Unsupported format '{item.strip()}'. Allowed formats: {', '.join(WEB_FETCH_FORMATS)}."
            )
        if value not in formats:
            formats.append(value)

    return formats


def parse_headers(raw_headers: Any) -> dict[str, str]:
    """
    Parses the `headers` JSON object. Headers without a name are dropped, because Web Fetch fails the whole fetch on
    them.
    """
    headers = parse_json_param(
        raw_headers,
        'Invalid JSON format in Headers (\'headers\'). Provide a JSON object, e.g. {"Accept-Language": "fr-FR"}.',
    )
    if not isinstance(headers, dict):
        raise ToolParameterValidationError(
            'Headers (\'headers\') must be a JSON object of header names and values, e.g. {"Accept-Language": "fr-FR"}.'
        )

    valid_headers: dict[str, str] = {}
    for name, value in headers.items():
        if not name.strip():
            continue
        if not isinstance(value, str):
            raise ToolParameterValidationError(f"The value of header '{name}' in Headers ('headers') must be a string.")
        valid_headers[name] = value
    return valid_headers


def parse_error_body(response: requests.Response) -> dict[str, Any] | None:
    try:
        body = response.json()
    except ValueError:
        return None
    return body if isinstance(body, dict) else None


def get_web_fetch_error(body: dict[str, Any] | None) -> tuple[str, str] | None:
    """
    Returns `(code, error)` when the body is Web Fetch's own flat `{code, error}` error envelope.
    """
    if body is None:
        return None
    code, error = body.get("code"), body.get("error")
    if isinstance(code, str) and isinstance(error, str):
        return code, error
    return None


def is_retryable(response: requests.Response) -> bool:
    if response.status_code < 500 and response.status_code != 429:
        return False
    return get_web_fetch_error(parse_error_body(response)) is None


def raise_web_fetch_error(response: requests.Response) -> None:
    """
    Maps a failed Web Fetch response to a ToolInvokeError. Web Fetch reports its own failures as a flat
    `{code, error}`; the Apify platform in front of it (auth, rate limits) as `{error: {type, message}}`.
    """
    body = parse_error_body(response)

    web_fetch_error = get_web_fetch_error(body)
    if web_fetch_error:
        # These describe the target URL rather than Apify (e.g. 502 UPSTREAM_FETCH_ERROR), so the message is shown
        # as-is, without the Apify API error prefix and status hints.
        code, error = web_fetch_error
        raise ToolInvokeError(f"{error} (Web Fetch error code: {code})")

    error = body.get("error") if body else None
    if isinstance(error, dict) and isinstance(error.get("message"), str):
        raise_apify_response_error(ACTION, error["message"], response.status_code)

    detail = response.text.strip()[:500] or response.reason or "empty response"
    raise_apify_response_error(ACTION, f"HTTP {response.status_code}: {detail}", response.status_code)


class WebFetch(Tool):
    def _invoke(
        self,
        tool_parameters: dict[str, Any],
    ) -> Generator[ToolInvokeMessage, None, None]:
        """
        Fetches a single URL through the Apify Web Fetch Actor's Standby endpoint and returns its response envelope
        as-is.
        """
        url = require_param(tool_parameters, "url", "URL is a required parameter.")
        url = validate_url(url)
        formats = parse_formats(tool_parameters.get("formats"))
        headers = parse_headers(tool_parameters.get("headers"))

        try:
            token = get_apify_token(self.runtime.credentials, self.runtime.credential_type)

            body: dict[str, Any] = {"url": url}
            if formats:
                body["formats"] = formats
            if headers:
                body["headers"] = headers

            deadline = time.monotonic() + TOTAL_TIMEOUT_SECS
            attempt = 0
            while True:
                response = requests.post(
                    WEB_FETCH_STANDBY_URL,
                    json=body,
                    headers={**TRACKING_HEADER, "Authorization": f"Bearer {token}"},
                    timeout=(CONNECT_TIMEOUT_SECS, max(deadline - time.monotonic(), 1)),
                )
                backoff = RETRY_BACKOFF_SECS * 2**attempt
                if (
                    response.ok
                    or attempt >= MAX_RETRIES
                    or not is_retryable(response)
                    or time.monotonic() + backoff >= deadline
                ):
                    break
                time.sleep(backoff)
                attempt += 1

            if not response.ok:
                raise_web_fetch_error(response)

            try:
                envelope = response.json()
            except ValueError:
                envelope = None
            if not isinstance(envelope, dict):
                raise ToolInvokeError(f"Web Fetch returned an unexpected response for URL: {url}")

            yield self.create_variable_message("result", envelope)

        except PASSTHROUGH_ERRORS:
            raise
        except requests.Timeout as e:
            raise ToolInvokeError(
                f"Fetching {url} took more than {TOTAL_TIMEOUT_SECS} seconds. "
                "The website may be slow or too large. Try again, or use a different URL."
            ) from e
        except Exception as e:
            raise_unexpected_error(ACTION, e)
