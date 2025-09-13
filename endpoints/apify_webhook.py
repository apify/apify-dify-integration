import json
from typing import Any, Mapping

from werkzeug import Request, Response
from dify_plugin import Endpoint


class ApifyWebhookEndpoint(Endpoint):
    def _invoke(
        self,
        r: Request,
        values: Mapping[str, Any],
        settings: Mapping[str, Any],
    ) -> Response:
        app_id = settings["app_selector"]["app_id"]

        try:
            request_body = r.get_json()
            print("PATH", r.path)
            resource = request_body.get("resource", {})
            if not isinstance(resource, dict):
                print("Invalid 'resource' type: expected object, got %s", type(resource).__name__)
                return Response(
                    json.dumps({"error": "'resource' must be an object"}), status=400, content_type="application/json"
                )
            workflow_response = self.session.app.workflow.invoke(
                app_id=app_id, inputs=request_body, response_mode="blocking"
            )

            return Response(
                json.dumps(workflow_response),
                status=200,
                content_type="application/json",
            )

        except Exception as e:
            print(f"An error occurred: {e}")
            error_payload = {
                "status": "error",
                "message": "An internal error occurred while processing the webhook.",
                "details": str(e),
            }

            return Response(
                json.dumps(error_payload),
                status=500,
                mimetype="application/json",
            )
