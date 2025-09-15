import json
from typing import Any, Mapping, Dict
from werkzeug import Request, Response
from dify_plugin import Endpoint


class ApifyWebhookEndpoint(Endpoint):
    def _invoke(
        self,
        r: Request,
        values: Mapping[str, Any],
        settings: Mapping[str, Any],
    ) -> Response:
        request_body = r.get_json()
        app_id = settings.get("app_selector").get("app_id")

        if not app_id or not isinstance(app_id, str):
            return Response(json.dumps({"error": "app_id not configured"}), status=404, mimetype="application/json")

        path: str = (r.path or "").strip()

        if path.endswith("/apify-chatflow-webhook-callback"):
            query = request_body.get("query")

            if not isinstance(query, str) or not query:
                return Response(
                    json.dumps({"error": "query must be a non-empty string"}),
                    status=400,
                    mimetype="application/json",
                )

            def stream_generator():
                try:
                    response_generator = self.session.app.chat.invoke(
                        app_id=app_id,
                        query=query,
                        inputs=self._flatten_dict(request_body),
                        response_mode="streaming",
                    )

                    for data in response_generator:
                        yield f"data: {json.dumps(data)}\n\n"

                except Exception as e:
                    error_data = {"error": f"Error during stream: {str(e)}"}
                    yield f"data: {json.dumps(error_data)}\n\n"

            return Response(
                stream_generator(),
                status=200,
                mimetype="text/event-stream",
            )

        if path.endswith("/apify-workflow-webhook-callback"):
            try:
                dify_resp = self.session.app.workflow.invoke(
                    app_id=app_id,
                    inputs=self._flatten_dict(request_body),
                    response_mode="blocking",
                )

                return Response(
                    response=dify_resp,
                    status=200,
                    content_type="application/json",
                )
            except Exception as e:
                print("WORKFLOW", e)
                return Response(json.dumps({"error": str(e)}), status=500, mimetype="application/json")

        return Response(json.dumps({"error": "Invalid webhook path"}), status=404, mimetype="application/json")

    def _flatten_dict(self, data: Any, parent_key: str = "", sep: str = "__") -> Dict[str, Any]:
        items: Dict[str, Any] = {}

        def _flatten(value: Any, current_key: str) -> None:
            if isinstance(value, dict):
                for k, v in value.items():
                    new_key = f"{current_key}{sep}{k}" if current_key else str(k)
                    _flatten(v, new_key)
            elif isinstance(value, list):
                for idx, v in enumerate(value):
                    new_key = f"{current_key}{sep}{idx}" if current_key else str(idx)
                    _flatten(v, new_key)
            else:
                items[current_key] = value

        _flatten(data, parent_key)
        return items
