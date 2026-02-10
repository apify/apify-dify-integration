import json
from typing import Any, Mapping, Dict
from werkzeug import Request, Response
from werkzeug.exceptions import BadRequest
from dify_plugin import Endpoint
from enum import Enum
from http import HTTPStatus


class DifyResponseMode(Enum):
    STREAMING = "streaming"
    BLOCKING = "blocking"


class ApifyWebhookEndpoint(Endpoint):
    def _invoke(
        self,
        r: Request,
        values: Mapping[str, Any],
        settings: Mapping[str, Any],
    ) -> Response:
        try:
            request_body = r.get_json()
        except BadRequest:
            return Response(
                json.dumps({"error": "Invalid JSON body"}),
                status=HTTPStatus.BAD_REQUEST,
                mimetype="application/json",
            )

        if request_body is None:
            return Response(
                json.dumps({"error": "Missing JSON body"}),
                status=HTTPStatus.BAD_REQUEST,
                mimetype="application/json",
            )

        app_selector = settings.get("app_selector") if isinstance(settings, Mapping) else None
        app_id = (app_selector or {}).get("app_id") if isinstance(app_selector, Mapping) else None

        if not app_id or not isinstance(app_id, str):
            return Response(
                json.dumps({"error": "app_id not configured"}), status=HTTPStatus.NOT_FOUND, mimetype="application/json"
            )

        path: str = (r.path or "").strip()

        if path.endswith("/apify-chatflow-webhook-callback"):
            query = request_body.get("query")

            if not isinstance(query, str) or not query:
                return Response(
                    json.dumps({"error": "query must be a non-empty string"}),
                    status=HTTPStatus.BAD_REQUEST,
                    mimetype="application/json",
                )

            def stream_generator():
                try:
                    response_generator = self.session.app.chat.invoke(
                        app_id=app_id,
                        query=query,
                        inputs=self._flatten_dict(request_body),
                        response_mode=DifyResponseMode.STREAMING,
                    )

                    for data in response_generator:
                        yield f"data: {json.dumps(data)}\n\n"

                except Exception as e:
                    error_data = {"error": f"Error during stream: {str(e)}"}
                    yield f"data: {json.dumps(error_data)}\n\n"

            return Response(
                stream_generator(),
                status=HTTPStatus.OK,
                mimetype="text/event-stream",
            )

        if path.endswith("/apify-workflow-webhook-callback"):
            try:
                dify_resp = self.session.app.workflow.invoke(
                    app_id=app_id,
                    inputs=self._flatten_dict(request_body),
                    response_mode=DifyResponseMode.BLOCKING,
                )

                return Response(
                    response=dify_resp if isinstance(dify_resp, str) else json.dumps(dify_resp),
                    status=HTTPStatus.OK,
                    content_type="application/json",
                )
            except Exception as e:
                print("An error occurred in workflow", e)
                return Response(
                    json.dumps({"error": str(e)}), status=HTTPStatus.INTERNAL_SERVER_ERROR, mimetype="application/json"
                )

        return Response(
            json.dumps({"error": "Invalid webhook path"}), status=HTTPStatus.NOT_FOUND, mimetype="application/json"
        )

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
