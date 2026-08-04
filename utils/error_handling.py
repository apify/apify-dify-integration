import json
import math
from urllib.parse import urlparse
from typing import Any

from apify_client.errors import ApifyApiError
try:
    from dify_plugin.errors.tool import ToolInvokeError, ToolParameterValidationError
except ImportError:
    class ToolInvokeError(Exception):
        pass

    class ToolParameterValidationError(Exception):
        pass


# Errors that already carry a deliberate, user-facing message. A tool's catch-all handler must
# re-raise these untouched, otherwise they get re-wrapped as "Unexpected error while ..." and the
# real message is buried behind a prefix that wrongly implies an unhandled crash.
PASSTHROUGH_ERRORS = (ToolInvokeError, ToolParameterValidationError)


def validate_number(
    value: Any,
    *,
    min_val: int | float | None = None,
    max_val: int | float | None = None,
    param_name: str = "parameter",
) -> int | float | None:
    """
    Validate a numeric parameter. Returns None if value is None (for optional params).
    Raises ToolParameterValidationError if value is not a number or is outside min/max.
    Rejects booleans and non-finite floats (NaN, inf).
    """
    if value is None:
        return None
    if isinstance(value, bool):
        raise ToolParameterValidationError(f"{param_name} must be a number.")
    if not isinstance(value, (int, float)):
        raise ToolParameterValidationError(f"{param_name} must be a number.")
    if isinstance(value, float) and not math.isfinite(value):
        raise ToolParameterValidationError(f"{param_name} must be a finite number.")
    if min_val is not None and value < min_val:
        raise ToolParameterValidationError(f"{param_name} must be at least {min_val}.")
    if max_val is not None and value > max_val:
        raise ToolParameterValidationError(f"{param_name} must be at most {max_val}.")
    return value


def validate_url(url: str, param_name: str = "url") -> str:
    """
    Validates that the value is a well-formed HTTP/HTTPS URL (scheme, host present, host not
    starting with a dot, path without '..' segments). Raises ToolParameterValidationError if invalid.
    """
    if url is None or not isinstance(url, str):
        raise ToolParameterValidationError(f"{param_name} must be a non-empty string.")
    url = url.strip()
    if not url:
        raise ToolParameterValidationError(f"{param_name} must be a non-empty string.")
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ToolParameterValidationError(
            f"{param_name} must be a valid HTTP or HTTPS URL (e.g. https://example.com)."
        )
    if not parsed.netloc:
        raise ToolParameterValidationError(
            f"{param_name} must be a valid URL with a host (e.g. https://example.com)."
        )
    if parsed.netloc.startswith("."):
        raise ToolParameterValidationError(
            f"{param_name} is not a valid URL (host must not start with a dot)."
        )

    for segment in parsed.path.split("/"):
        if segment.startswith(".."):
            raise ToolParameterValidationError(
                f"{param_name} is not a valid URL (path segments must not start with '..')."
            )

    return url


def require_param(tool_parameters: dict[str, Any], key: str, message: str | None = None) -> Any:
    value = tool_parameters.get(key)
    if not value:
        raise ToolParameterValidationError(message or f"{key} is a required parameter.")
    return value


def parse_json_param(raw_value: str | None, error_message: str) -> Any:
    try:
        if raw_value is None or not str(raw_value).strip():
            return {}
        if isinstance(raw_value, (dict, list)):
            return raw_value
        return json.loads(raw_value)
    except json.JSONDecodeError as exc:
        raise ToolParameterValidationError(error_message) from exc


# Hints appended to Apify API errors. Only codes whose hint is actionable are listed; for others
# Apify's own message is already specific enough.
_STATUS_HINTS = {
    401: "authentication failed - check your Apify token",
    403: "access is forbidden - your account may lack permission for this resource",
    429: "Apify rate limit exceeded - please retry later",
}


def raise_apify_error(action: str, exc: ApifyApiError) -> None:
    detail = exc.message or str(exc)
    hint = _STATUS_HINTS.get(getattr(exc, "status_code", None))
    if getattr(exc, "status_code", None) is not None and exc.status_code >= 500 and hint is None:
        hint = "Apify is experiencing a server error - please retry later"
    message = f"Apify API error while {action}: {detail}"
    if hint:
        message += f" ({hint})"
    raise ToolInvokeError(message) from exc


def raise_unexpected_error(action: str, exc: Exception) -> None:
    message = f"Unexpected error while {action}: {exc}"
    raise ToolInvokeError(message) from exc
