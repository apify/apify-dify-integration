from collections.abc import Generator
from typing import Any

from apify_client.errors import ApifyApiError
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools.client import get_apify_client
from utils.error_handling import raise_apify_error, raise_unexpected_error, require_param

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
        url = require_param(tool_parameters, "url", "URL is a required parameter.")

        crawler_type = tool_parameters.get("crawler_type", "playwright:adaptive")

        try:
            client = get_apify_client(self.runtime.credentials, self.runtime.credential_type)

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
            raise_apify_error("scraping URL", e)
        except Exception as e:
            raise_unexpected_error("scraping URL", e)
