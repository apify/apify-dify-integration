import base64
from collections.abc import Generator
from typing import Any

from apify_client.errors import ApifyApiError
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools.client import get_apify_client


class GetKeyValueStoreRecord(Tool):
    def _invoke(
        self,
        tool_parameters: dict[str, Any],
    ) -> Generator[ToolInvokeMessage, None, None]:
        """
        Retrieves a single record from a specified Apify key-value store.
        Handles different content types (JSON, text, binary).
        """
        store_id = tool_parameters.get("storeId")
        if not store_id:
            yield self.create_text_message("Error: Store ID ('storeId') is a required parameter.")
            return

        record_key = tool_parameters.get("recordKey")
        if not record_key:
            yield self.create_text_message("Error: Record Key ('recordKey') is a required parameter.")
            return

        try:
            client = get_apify_client(self.runtime.credentials, self.runtime.credential_type)
            record = client.key_value_store(store_id).get_record(record_key)
            if not record:
                raise Exception(f"Record with key '{record_key}' not found in store '{store_id}'.")

            record_value = record.get("value")
            content_type = record.get("contentType", "application/octet-stream")  # Default to binary if no content type
            processed_value = None

            # Handle Different Formats
            if isinstance(record_value, bytes):
                # If the content type indicates text or json, decode it.
                if "text" in content_type or "json" in content_type:
                    processed_value = record_value.decode("utf-8")
                else:
                    # Otherwise, it's binary data; encode it in Base64.
                    processed_value = base64.b64encode(record_value).decode("ascii")
            else:
                # If it's not bytes, the client has already parsed it. We will use it as is.
                processed_value = record_value

            output = {"result": processed_value, "contentType": content_type}

            yield self.create_json_message(output)

        except ApifyApiError as e:
            error_message = f"An Apify API error occurred: {e.message or str(e)}"
            yield self.create_text_message(error_message)
        except Exception as e:
            error_message = f"An unexpected error occurred: {e}"
            yield self.create_text_message(error_message)
