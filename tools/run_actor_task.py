from collections.abc import Generator
from typing import Any

from apify_client.errors import ApifyApiError
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools.client import get_apify_client
from utils.error_handling import (
    parse_json_param,
    raise_apify_error,
    raise_unexpected_error,
    require_param,
    validate_number,
)


class RunTask(Tool):
    def _invoke(
        self,
        tool_parameters: dict[str, Any],
    ) -> Generator[ToolInvokeMessage, None, None]:
        """
        Invokes a pre-configured Apify actor task, either waiting for it to finish
        or starting it and returning immediately.
        """
        task_id = require_param(tool_parameters, "taskId", "Task ID ('taskId') is a required parameter.")

        input_override_str = tool_parameters.get("input_override", "{}")
        input_override = parse_json_param(input_override_str, "Invalid JSON format in Input Override.")

        wait_for_finish = tool_parameters.get("wait_for_finish", False)
        build = tool_parameters.get("build")
        timeout_secs = validate_number(
            tool_parameters.get("timeout"),
            min_val=0,
            param_name="timeout",
        )
        memory_mb = tool_parameters.get("memory")

        try:
            client = get_apify_client(self.runtime.credentials, self.runtime.credential_type)
            task_client = client.task(task_id)

            task_options = {
                "build": build,
                "timeout_secs": timeout_secs,
                "memory_mbytes": memory_mb,
            }
            filtered_options = {k: v for k, v in task_options.items() if v is not None}

            if wait_for_finish:
                # Synchronous Execution: starts the task and waits for it to finish.
                run_details = task_client.call(task_input=input_override, **filtered_options)
            else:
                # Asynchronous Execution: starts the task and returns immediately.
                run_details = task_client.start(task_input=input_override, **filtered_options)

            yield self.create_variable_message("result", run_details)

        except ApifyApiError as e:
            raise_apify_error("running task", e)
        except Exception as e:
            raise_unexpected_error("running task", e)
