from collections.abc import Generator, Mapping
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage


def result_messages(
    tool: Tool,
    payload: Mapping[str, Any] | list[Any],
    agent_payload: Mapping[str, Any] | list[Any] | None = None,
) -> Generator[ToolInvokeMessage, None, None]:
    """
    Yields a tool's result for both kinds of Dify caller. Agents read only text and JSON messages and skip
    variables, so they get a JSON message. Workflows select fields from the `result` variable described by the
    tool's `output_schema`, so they get the variable.

    Args:
        tool: The tool yielding the result
        payload: The full result, returned as the `result` variable
        agent_payload: A smaller result for agents, if the full one costs too much context; defaults to `payload`
    """
    yield tool.create_json_message(payload if agent_payload is None else agent_payload)
    yield tool.create_variable_message("result", payload)
