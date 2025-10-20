from collections.abc import Generator
from typing import Any

from apify_client.errors import ApifyApiError
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools.client import get_apify_client


class GetDatasetItems(Tool):
    def _invoke(
        self,
        tool_parameters: dict[str, Any],
    ) -> Generator[ToolInvokeMessage, None, None]:
        """
        Retrieves items from a specified Apify dataset, with optional pagination.
        """
        dataset_id = tool_parameters.get("datasetId")
        if not dataset_id:
            yield self.create_text_message("Error: Dataset ID ('datasetId') is a required parameter.")
            return

        limit = tool_parameters.get("limit")
        offset = tool_parameters.get("offset")

        try:
            client = get_apify_client(self.runtime.credentials, self.runtime.credential_type)
            dataset_client = client.dataset(dataset_id)
            list_options = {
                "limit": limit,
                "offset": offset,
            }
            filtered_options = {k: v for k, v in list_options.items() if v is not None}
            dataset_items_list = dataset_client.list_items(**filtered_options).items
            output_data = {"result": dataset_items_list}

            yield self.create_json_message(output_data)

        except ApifyApiError as e:
            error_message = f"An Apify API error occurred: {e.message or str(e)}"
            yield self.create_text_message(error_message)
        except Exception as e:
            error_message = f"An unexpected error occurred: {e}"
            yield self.create_text_message(error_message)
