from collections.abc import Generator
from typing import Any

from apify_client.errors import ApifyApiError
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools.client import get_apify_client
from utils.error_handling import parse_json_param, raise_apify_error, raise_unexpected_error, require_param


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
            raise_apify_error("running actor", e)
        except Exception as e:
            raise_unexpected_error("running actor", e)
