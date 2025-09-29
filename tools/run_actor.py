import json
from collections.abc import Generator
from typing import Any

from apify_client.errors import ApifyApiError
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools.client import get_apify_client


class RunActor(Tool):
    def _invoke(
        self,
        tool_parameters: dict[str, Any],
    ) -> Generator[ToolInvokeMessage, None, None]:
        """
        Synchronously invokes an Apify actor, either waiting for it to finish or starting it
        and returning immediately.
        """
        actor_id = tool_parameters.get("actorId")
        if not actor_id:
            yield self.create_text_message("Error: Actor ID ('actorId') is a required parameter.")
            return

        input_body_str = tool_parameters.get("input_body", "{}")
        try:
            run_input = json.loads(input_body_str)
        except json.JSONDecodeError:
            yield self.create_text_message("Error: Invalid JSON format in Input Body ('input_body').")
            return

        wait_for_finish = tool_parameters.get("wait_for_finish", False)
        build = tool_parameters.get("build")
        timeout_secs = tool_parameters.get("timeout")
        memory_mb = tool_parameters.get("memory")

        try:
            client = get_apify_client(self.runtime)
            actor_client = client.actor(actor_id)

            run_options = {
                "build": build,
                "timeout_secs": timeout_secs,
                "memory_mbytes": memory_mb,
            }
            filtered_options = {k: v for k, v in run_options.items() if v is not None}

            run_details = None

            if wait_for_finish:
                # Synchronous Execution
                run_details = actor_client.call(run_input=run_input, **filtered_options)
            else:
                # Asynchronous Execution
                run_details = actor_client.start(run_input=run_input, **filtered_options)

            output_data = {"result": run_details}

            yield self.create_json_message(output_data)

        except ApifyApiError as e:
            error_message = f"An Apify API error occurred: {e.message or str(e)}"
            yield self.create_text_message(error_message)
        except Exception as e:
            error_message = f"An unexpected error occurred: {e}"
            yield self.create_text_message(error_message)
