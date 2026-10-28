# AGENTS.md

Guidance for coding agents working in this repository. `CLAUDE.md` is only an `@AGENTS.md` pointer,
so put instructions here and leave the pointer alone. `.github/workflows/agents-md-maintenance.yml`
updates this file inside each PR that changes the code.

## Project

A Python [Dify](https://dify.ai) plugin (`apify-integration` in `manifest.yaml`) that exposes the
Apify platform to Dify apps. It ships two kinds of entrypoint, both declared in `manifest.yaml`:

- **Tools** (`provider/apify.yaml` → `tools/*.yaml` + `tools/*.py`): Run Actor, Run Actor Task,
  Web Fetch (calls the `apify/web-fetch` Actor's Standby endpoint), Scrape Single URL (deprecated in
  favor of Web Fetch; calls `apify/website-content-crawler` with `maxCrawlPages: 1`), Get Dataset
  Items, Get Key-Value Store Record.
- **Webhook endpoints** (`group/apify_webhook.yaml` → `endpoints/*.yaml`): an Apify webhook POSTs to
  `/apify-workflow-webhook-callback` or `/apify-chatflow-webhook-callback`, which invokes the Dify
  app chosen in the endpoint's `app_selector` setting.

The plugin stores nothing; Dify holds the credentials and passes them in at runtime. Released
packages (`.difypkg`) are published to the Dify Marketplace through `langgenius/dify-plugins`.

## Commands

```bash
uv venv && uv pip install -e ".[dev]"   # what CI does; Python 3.12
flake8 .                                # the lint CI runs (ruff is configured too, not run in CI)
dify plugin package . -o apify.difypkg  # packaging validation; needs the Dify Plugin CLI binary
cp .env.example .env && python -m main  # remote debug against Dify; set REMOTE_INSTALL_KEY first
```

There are no tests. `test.yml` (PRs to `main`) runs flake8 and `dify plugin package`; `release.yml`
does the same on `v*` tags and attaches `apify.difypkg` to a GitHub release. The Dify CLI is
installed in CI from the `dify-plugin-daemon` releases page; locally see `CONTRIBUTING.md`.

## Architecture

- **Wiring is by YAML, not imports.** Each `tools/<name>.yaml` names its Python file under
  `extra.python.source` and is listed in `provider/apify.yaml`; endpoint YAMLs do the same for
  `endpoints/apify_webhook.py`. A new tool needs the `.py`, the `.yaml`, and a line in
  `provider/apify.yaml`. Parameter names in the YAML (`actorId`, `input_body`, `wait_for_finish`,
  …) are the keys the `.py` reads from `tool_parameters` — rename both together.
- **Two credential types.** `provider/apify.py` implements both an API-token credential
  (`apify_token`) and OAuth (`access_token`/`refresh_token` against `console-backend.apify.com`).
  `tools/client.py::get_apify_client` picks the token by `self.runtime.credential_type`; always
  build clients through it — it also sets the `x-apify-integration-platform: dify` tracking header
  via `ApifyClient(token, headers=...)`. Calls that bypass `ApifyClient` (Web Fetch) get the token
  from `get_apify_token` and must send `TRACKING_HEADER` themselves.
- **apify-client v3 returns Pydantic models, not dicts.** Dify cannot serialize them, so run
  objects go through `run_to_dict()` in `tools/client.py` before being yielded (camelCase keys via
  `by_alias`, trailing `/` stripped from `containerUrl`). Attributes are snake_case
  (`run.default_dataset_id`, `build.actor_definition`). Run options are `run_timeout` as a
  `timedelta` and `memory_mbytes`; `actor.call()` / `task.call()` can return `None`, which the tools
  turn into a `ToolInvokeError`.
- **Return results with `yield from result_messages(self, payload)`** (`utils/messages.py`), never a
  bare `create_variable_message`. Dify agents skip variable messages and read only text and JSON,
  so the helper yields a JSON message for agents and the `result` variable (fields per
  `output_schema`) for workflows. Its optional `agent_payload` sends agents a smaller JSON.
- **Run Actor prefill.** When `input_body` is empty, `run_actor.py` reads the default build's input
  schema and uses each property's `prefill` as input.
- **Web Fetch talks HTTP, not `ApifyClient`.** `web_fetch.py` POSTs to
  `https://web-fetch.apify.actor/` with `requests` and yields the response envelope as-is. It
  retries only Apify platform errors (5xx, 429); Web Fetch's own flat `{code, error}` errors are
  final, because the Actor already retries the target. `formats` deliberately has no YAML default:
  when it is empty the tool omits it, so the Actor picks the format by content type (raw for
  images). A default would make binary URLs fail.
- **Webhook payload flattening.** `ApifyWebhookEndpoint._flatten_dict` flattens the Apify webhook
  body into `__`-joined keys (`resource__defaultDatasetId`) because Dify app inputs are flat. The
  workflow path responds in blocking mode; the chatflow path streams SSE and requires a non-empty
  string `query` in the body.
- `main.py` lowers `MAX_REQUEST_TIMEOUT` to 120 s (the `dify_plugin` default is 300). Keep that in
  mind for synchronous runs (`wait_for_finish`, Scrape Single URL), which block until the Apify run
  ends. Web Fetch stops waiting at 110 s (`TOTAL_TIMEOUT_SECS`) to report a clear timeout first.

## Conventions and gotchas

- **Error handling pattern** (`utils/error_handling.py`): validate inputs with `require_param`,
  `validate_number`, `validate_url`, `parse_json_param` (they raise
  `ToolParameterValidationError`), then wrap the API work as
  `except PASSTHROUGH_ERRORS: raise` → `except ApifyApiError: raise_apify_error(...)` →
  `except Exception: raise_unexpected_error(...)`. Keep the passthrough clause first, or deliberate
  messages get re-wrapped as "Unexpected error while ...". For Apify error responses received
  outside `ApifyClient`, use `raise_apify_response_error`, which uses the same message format.
- **Never put secrets in OAuth errors.** `provider/apify.py` reports token-endpoint failures only via
  `_safe_oauth_error_detail()` (HTTP status plus `OAUTH_SAFE_ERROR_KEYS`) and deliberately omits
  `str(e)`, which can contain the request payload with `client_secret`. Don't reintroduce raw
  response bodies or exception text.
- **Dify Marketplace rules** (enforced on submission, not by CI):
  - every dependency has both a lower and an upper bound (what got 1.2.0 through review, #45), in
    `pyproject.toml` *and* `requirements.txt` — keep the runtime dependency lists identical;
  - the package must contain runtime files only: dev-only files are listed in `.difyignore`
    (currently `CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md`, `.flake8`). Add any new dev-only file there;
  - `manifest.yaml` must keep its `repo` and `contact` fields.
- **Releasing**: bump both `version` and `meta.version` in `manifest.yaml` (keep them equal), merge
  to `main`, publish a GitHub release tagged `v<version>`, then submit the built `.difypkg` as a PR
  to `langgenius/dify-plugins` (steps in `CONTRIBUTING.md`). `manifest.yaml` also pins
  `minimum_dify_version` and the 256 MB memory limit. The `version` in `pyproject.toml` (`0.1.0`) is not the plugin version.
- Python style: flake8/ruff at line length 120, target py312. Conventional commits (`feat:`,
  `fix:`, `ci:`, `docs:`, `chore:`), feature branches with PRs to `main`.
