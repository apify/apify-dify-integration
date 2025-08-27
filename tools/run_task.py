import json
from collections.abc import Generator
from typing import Any

from apify_client import ApifyClient
from apify_client.errors import ApifyApiError
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage


class RunTask(Tool):
    def _invoke(
        self,
        tool_parameters: dict[str, Any],
    ) -> Generator[ToolInvokeMessage, None, None]:
        """
        Invokes a pre-configured Apify actor task, either waiting for it to finish
        or starting it and returning immediately.
        """
        api_token = self.runtime.credentials.get("apify_token")
        if not api_token:
            yield self.create_text_message("Error: Apify API Token not found in credentials.")
            return

        task_id = tool_parameters.get("taskId")
        if not task_id:
            yield self.create_text_message("Error: Task ID ('taskId') is a required parameter.")
            return

        input_override_str = tool_parameters.get("input_override", "{}")
        try:
            input_override = json.loads(input_override_str)
        except json.JSONDecodeError:
            yield self.create_text_message("Error: Invalid JSON format in Input Override.")
            return

        wait_for_finish = tool_parameters.get("wait_for_finish", False)
        build = tool_parameters.get("build")
        timeout_secs = tool_parameters.get("timeout")
        memory_mb = tool_parameters.get("memory")

        try:
            client = ApifyClient(token=api_token, timeout_secs=360)
            task_client = client.task(task_id)

            task_options = {
                "build": build,
                "timeout_secs": timeout_secs,
                "memory_mbytes": memory_mb,
            }
            filtered_options = {k: v for k, v in task_options.items() if v is not None}

            run_details = None

            if wait_for_finish:
                # Synchronous Execution: starts the task and waits for it to finish.
                run_details = task_client.call(task_input=input_override, **filtered_options)
            else:
                # Asynchronous Execution: starts the task and returns immediately.
                run_details = task_client.start(task_input=input_override, **filtered_options)

            output_data = {"result": run_details}

            yield self.create_json_message(output_data)

        except ApifyApiError as e:
            error_message = f"An Apify API error occurred: {e.message or str(e)}"
            yield self.create_text_message(error_message)
        except Exception as e:
            error_message = f"An unexpected error occurred: {e}"
            yield self.create_text_message(error_message)
