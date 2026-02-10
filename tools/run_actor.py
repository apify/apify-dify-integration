from collections.abc import Generator
from typing import Any

from apify_client.errors import ApifyApiError
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools.client import get_apify_client
from utils.error_handling import parse_json_param, raise_apify_error, raise_unexpected_error, require_param


def get_prefilled_input(actor_client: Any) -> dict[str, Any]:
    """
    Fetches the default build of the actor and extracts prefill values from the input schema.
    """
    try:
        # In Dify environment, sometimes these calls return coroutines
        # even when using the synchronous ApifyClient.
        import asyncio
        import inspect

        def run_sync(coro_or_val: Any) -> Any:
            if inspect.iscoroutine(coro_or_val):
                return asyncio.run(coro_or_val)
            return coro_or_val

        build_client = run_sync(actor_client.default_build())
        build = run_sync(build_client.get())

        if not build:
            return {}

        actor_definition = build.get("actorDefinition", {})
        input_schema = actor_definition.get("input", {})
        properties = input_schema.get("properties", {})

        if not properties:
            return {}

        default_values: dict[str, Any] = {}

        for key, property_info in properties.items():
            prefill = property_info.get("prefill")
            if prefill is not None:
                default_values[key] = prefill

        return default_values
    except Exception:
        return {}


class RunActor(Tool):
    def _invoke(
        self,
        tool_parameters: dict[str, Any],
    ) -> Generator[ToolInvokeMessage, None, None]:
        """
        Synchronously invokes an Apify actor, either waiting for it to finish or starting it
        and returning immediately.
        """
        actor_id = require_param(tool_parameters, "actorId", "Actor ID ('actorId') is a required parameter.")

        input_body_str = tool_parameters.get("input_body", "{}")
        run_input = parse_json_param(input_body_str, "Invalid JSON format in Input Body ('input_body').")

        wait_for_finish = tool_parameters.get("wait_for_finish", False)
        build = tool_parameters.get("build")
        timeout_secs = tool_parameters.get("timeout")
        memory_mb = tool_parameters.get("memory")

        try:
            client = get_apify_client(self.runtime.credentials, self.runtime.credential_type)
            actor_client = client.actor(actor_id)

            # If no input is provided, fetch prefilled values from the actor's default build
            if not run_input:
                prefilled_input = get_prefilled_input(actor_client)
                if prefilled_input:
                    run_input = prefilled_input

            run_options = {
                "build": build,
                "timeout_secs": timeout_secs,
                "memory_mbytes": memory_mb,
            }
            filtered_options = {k: v for k, v in run_options.items() if v is not None}

            if wait_for_finish:
                # Synchronous Execution
                run_details = actor_client.call(run_input=run_input, **filtered_options)
            else:
                # Asynchronous Execution
                run_details = actor_client.start(run_input=run_input, **filtered_options)
            yield self.create_variable_message("result", run_details)

        except ApifyApiError as e:
            raise_apify_error("running actor", e)
        except Exception as e:
            raise_unexpected_error("running actor", e)
