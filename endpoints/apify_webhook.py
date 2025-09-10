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
            inputs = request_body.get("inputs", {})
            if not isinstance(inputs, dict):
                print("Invalid 'inputs' type: expected object, got %s", type(inputs).__name__)
                return Response(
                    json.dumps({"error": "'inputs' must be an object"}), status=400, content_type="application/json"
                )

            workflow_response = self.session.app.workflow.invoke(app_id=app_id, inputs=inputs, response_mode="blocking")

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
