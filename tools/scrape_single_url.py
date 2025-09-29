from collections.abc import Generator
from typing import Any

from apify_client.errors import ApifyApiError
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools.client import get_apify_client

WEBSITE_CONTENT_CRAWLER_ID = "apify/website-content-crawler"


class ScrapeSingleUrl(Tool):
    def _invoke(
        self,
        tool_parameters: dict[str, Any],
    ) -> Generator[ToolInvokeMessage, None, None]:
        """
        Invokes the Apify Website Content Crawler for a single URL. Either waiting for it to finish or starting it
        and returning immediately
        """
        url = tool_parameters.get("url")
        if not url:
            yield self.create_text_message("Error: URL is a required parameter.")
            return

        crawler_type = tool_parameters.get("crawler_type", "playwright:adaptive")

        try:
            client = get_apify_client(self.runtime)

            actor_input = {
                "startUrls": [{"url": url}],
                "crawlerType": crawler_type,
                "maxCrawlDepth": 0,
                "maxCrawlPages": 1,
                "maxResults": 1,
                "proxyConfiguration": {"useApifyProxy": True},
                "removeCookieWarnings": True,
                "saveHtmlToFile": True,
                "saveMarkdown": True,
            }

            actor_client = client.actor(WEBSITE_CONTENT_CRAWLER_ID)
            actor_result = actor_client.call(run_input=actor_input)
            dataset_id = actor_result["defaultDatasetId"]
            dataset_client = client.dataset(dataset_id)
            scraped_item = dataset_client.list_items().items[0]
            output_data = {"result": scraped_item}

            yield self.create_json_message(output_data)

        except ApifyApiError as e:
            error_message = f"An Apify API error occurred: {e.message or str(e)}"
            yield self.create_text_message(error_message)
        except Exception as e:
            error_message = f"An unexpected error occurred: {e}"
            yield self.create_text_message(error_message)
