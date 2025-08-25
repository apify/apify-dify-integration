from typing import Any, Dict, Generator

from apify_client import ApifyClient
from apify_client.errors import ApifyApiError

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

WEBSITE_CONTENT_CRAWLER_ID = 'aYG0l9s7dbB7j3gbS'

class ScrapeSingleUrl(Tool):
    def _invoke(
        self,
        tool_parameters: Dict[str, Any],
    ) -> Generator[ToolInvokeMessage, None, None]:
        """
        Invokes the Apify Website Content Crawler for a single URL. Either waiting for it to finish or starting it
        and returning immediately
        """
        api_token = self.runtime.credentials.get('apify_token')
        if not api_token:
            yield self.create_text_message("Error: Apify API Token not found in credentials.")
            return

        url = tool_parameters.get('url')
        if not url:
            yield self.create_text_message("Error: URL is a required parameter.")
            return

        crawler_type = tool_parameters.get('crawler_type', 'playwright:adaptive')
        wait_for_finish = tool_parameters.get('wait_for_finish', True)

        try:
            client = ApifyClient(token=api_token,timeout_secs=360)

            actor_input = {
                "startUrls": [{"url": url}],
                "crawlerType": crawler_type,
                "maxCrawlDepth": 0,
                "maxCrawlPages": 1,
                "maxResults": 1,
                "proxyConfiguration": {"useApifyProxy": True},
                "removeCookieWarnings": True,
                "saveHtmlToFile": True,
                "saveMarkdown": True
            }

            actor_client = client.actor(WEBSITE_CONTENT_CRAWLER_ID)

            run_details = None

            if wait_for_finish:
                # Synchronous Execution
                actor_result = actor_client.call(run_input=actor_input)
                dataset_id = actor_result['defaultDatasetId']
                dataset_client = client.dataset(dataset_id)
                run_details = dataset_client.list_items().items
            else:
                # Asynchronous Execution
                run_details = actor_client.start(run_input=actor_input)
            yield self.create_json_message(run_details)

        except ApifyApiError as e:
            error_message = f"An Apify API error occurred: {e.message or str(e)}"
            yield self.create_text_message(error_message)
        except Exception as e:
            error_message = f"An unexpected error occurred: {e}"
            yield self.create_text_message(error_message)