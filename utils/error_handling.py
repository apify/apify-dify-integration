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
    starting with a dot). Raises ToolParameterValidationError if invalid.
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


APIFY_RUN_FAILED_STATUSES = ("FAILED", "TIMED-OUT", "ABORTED")


def raise_if_run_failed(run_details: dict[str, Any], context: str = "Actor run") -> None:
    """
    If the run finished in a failed terminal state, raise ToolInvokeError so the tool
    is reported as failed. Only call this when wait_for_finish was True.
    """
    status = run_details.get("status")
    status_upper = str(status).upper() if status else ""
    if not status or status_upper not in APIFY_RUN_FAILED_STATUSES:
        return
    run_id = run_details.get("id", "")
    run_id_suffix = f" (run ID: {run_id})" if run_id else ""
    if status_upper == "ABORTED":
        message = f"{context} was aborted{run_id_suffix}. Check Apify Console for details."
    elif status_upper == "TIMED-OUT":
        message = f"{context} timed out{run_id_suffix}. Check Apify Console for details."
    else:
        message = (
            f"{context} finished with status {status}{run_id_suffix}. "
            "Check the run in Apify Console for details."
        )
    raise ToolInvokeError(message)


def raise_apify_error(action: str, exc: ApifyApiError) -> None:
    message = f"Apify API error while {action}: {exc.message or str(exc)}"
    raise ToolInvokeError(message) from exc


def raise_unexpected_error(action: str, exc: Exception) -> None:
    message = f"Unexpected error while {action}: {exc}"
    raise ToolInvokeError(message) from exc
