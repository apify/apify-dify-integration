import json
from typing import Any

from apify_client.errors import ApifyApiError
try:
    from dify_plugin.errors.tool import ToolInvokeError, ToolParameterValidationError
except ImportError:
    class ToolInvokeError(Exception):
        pass

    class ToolParameterValidationError(Exception):
        pass


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


def raise_apify_error(action: str, exc: ApifyApiError) -> None:
    message = f"Apify API error while {action}: {exc.message or str(exc)}"
    raise ToolInvokeError(message) from exc


def raise_unexpected_error(action: str, exc: Exception) -> None:
    message = f"Unexpected error while {action}: {exc}"
    raise ToolInvokeError(message) from exc
