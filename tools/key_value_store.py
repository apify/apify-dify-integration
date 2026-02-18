import mimetypes
from collections.abc import Generator
from typing import Any

from apify_client.errors import ApifyApiError
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from utils.error_handling import ToolInvokeError

from tools.client import get_apify_client
from utils.error_handling import raise_apify_error, raise_unexpected_error, require_param


def get_file_extension(content_type: str) -> str:
    """
    Returns file extension based on content type.
    """
    ext = mimetypes.guess_extension(content_type, strict=False)
    return ext or ""


def sanitize_filename(key: str) -> str:
    """
    Sanitizes a record key for use as a file name.
    """
    if not key:
        return key
    return key.strip().replace("\n", "").replace("\r", "")


def get_mime_type_from_extension(filename: str) -> str | None:
    """
    Infers MIME type from file extension.
    """
    mime_type, _ = mimetypes.guess_type(filename, strict=False)
    return mime_type


def is_binary_content_type(content_type: str) -> bool:
    """
    Determines if content type represents binary data.
    """
    if not content_type:
        return False

    if "application/json" in content_type or "text/" in content_type:
        return False

    return True


class GetKeyValueStoreRecord(Tool):
    def _invoke(
        self,
        tool_parameters: dict[str, Any],
    ) -> Generator[ToolInvokeMessage, None, None]:
        """
        Retrieves a single record from a specified Apify key-value store.
        Handles different content types (JSON, text, binary).
        """
        store_id = require_param(tool_parameters, "storeId", "Store ID ('storeId') is a required parameter.")

        record_key = require_param(tool_parameters, "recordKey", "Record Key ('recordKey') is a required parameter.")

        try:
            client = get_apify_client(self.runtime.credentials, self.runtime.credential_type)
            record = client.key_value_store(store_id).get_record(record_key)
            if not record:
                raise ToolInvokeError(f"Record with key '{record_key}' not found in store '{store_id}'.")

            record_value = record.get("value")
            content_type = record.get("contentType", "application/octet-stream")

            # Try to infer MIME type from the record key
            if content_type == "application/octet-stream":
                inferred_mime = get_mime_type_from_extension(record_key)
                if inferred_mime:
                    content_type = inferred_mime

            # Handle JSON data
            if "application/json" in content_type:
                # If it's bytes, decode it first
                if isinstance(record_value, bytes):
                    record_value = record_value.decode("utf-8")

                yield self.create_variable_message("result", {
                    "key": record_key,
                    "value": record_value,
                    "contentType": content_type,
                    "dataType": "json",
                })
                return

            # Handle binary files (images, PDFs, etc.)
            is_binary = is_binary_content_type(content_type)
            if is_binary and isinstance(record_value, bytes):
                file_extension = get_file_extension(content_type)
                base_name = sanitize_filename(record_key)
                # Avoid duplicate extension if name already ends with the extension
                if file_extension and base_name.lower().endswith(file_extension.lower()):
                    file_name = base_name
                else:
                    file_name = base_name + file_extension if file_extension else base_name

                blob_meta = {
                    "mime_type": content_type,
                    "file_name": file_name,
                }

                # Return the file as a downloadable blob with proper mime type
                yield self.create_blob_message(
                    blob=record_value,
                    meta=blob_meta
                )

                yield self.create_variable_message("result", {
                    "key": record_key,
                    "fileName": file_name,
                    "contentType": content_type,
                    "size": len(record_value),
                    "dataType": "file",
                })
                return

            # Handle text data
            if isinstance(record_value, bytes):
                record_value = record_value.decode("utf-8")

            yield self.create_variable_message("result", {
                "key": record_key,
                "value": record_value,
                "contentType": content_type,
                "dataType": "text",
            })

        except ApifyApiError as e:
            raise_apify_error("fetching store record", e)
        except Exception as e:
            raise_unexpected_error("fetching store record", e)
