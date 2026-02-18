from collections.abc import Generator
from typing import Any

from apify_client.errors import ApifyApiError
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools.client import get_apify_client
from utils.error_handling import (
    raise_apify_error,
    raise_unexpected_error,
    require_param,
    validate_number,
)


class GetDatasetItems(Tool):
    def _invoke(
        self,
        tool_parameters: dict[str, Any],
    ) -> Generator[ToolInvokeMessage, None, None]:
        """
        Retrieves items from a specified Apify dataset, with optional pagination.
        """
        dataset_id = require_param(tool_parameters, "datasetId", "Dataset ID ('datasetId') is a required parameter.")

        limit = validate_number(
            tool_parameters.get("limit"),
            min_val=1,
            param_name="limit",
        )
        offset = validate_number(
            tool_parameters.get("offset"),
            min_val=0,
            param_name="offset",
        )

        try:
            client = get_apify_client(self.runtime.credentials, self.runtime.credential_type)
            dataset_client = client.dataset(dataset_id)
            list_options = {
                "limit": limit,
                "offset": offset,
            }
            filtered_options = {k: v for k, v in list_options.items() if v is not None}
            dataset_items_list = dataset_client.list_items(**filtered_options).items

            yield self.create_variable_message("result", {
                "items": dataset_items_list,
                "count": len(dataset_items_list),
                "datasetId": dataset_id,
            })

        except ApifyApiError as e:
            raise_apify_error("fetching dataset items", e)
        except Exception as e:
            raise_unexpected_error("fetching dataset items", e)
