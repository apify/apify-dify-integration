# CLAUDE.md

## Project Purpose

A Dify plugin that integrates the [Apify](https://apify.com) platform into [Dify.ai](https://dify.ai) workflows. It allows users to run Apify Actors and Tasks, scrape URLs, retrieve datasets, and trigger workflows via webhooks — all from within Dify.

## Repository Structure

```
main.py                  # Plugin entry point (DifyPlugin with 120s timeout)
manifest.yaml            # Plugin metadata, version, permissions, entrypoints
pyproject.toml           # Python project config and dev tooling
requirements.txt         # Runtime dependencies
provider/
  apify.py               # OAuth provider: token exchange, refresh, credential validation
  apify.yaml             # Tool provider schema for OAuth
tools/
  client.py              # ApifyClient wrapper with telemetry tracking headers
  run_actor.py           # Execute an Apify Actor with custom input
  run_actor_task.py      # Execute a predefined Apify Task
  scrape_single_url.py   # Quick single-URL web scraping
  get_dataset_items.py   # Retrieve results from Apify datasets
  key_value_store.py     # Fetch records from an Apify Key-Value Store
  *.yaml                 # Tool schema definitions
endpoints/
  apify_webhook.py       # Webhook handler for Actor Run Finished triggers
  *.yaml                 # Webhook endpoint schemas (chatflow and workflow)
group/
  apify_webhook.yaml     # Webhook group configuration
utils/
  error_handling.py      # Shared error handling utilities
.github/workflows/
  test.yml               # Lint + Dify plugin validation on PRs to main
  release.yml            # Package and release .difypkg on version tags (v*)
  claude-md-maintenance.yml  # Auto-updates this file on pushes to main
```

## Technology Stack

- **Language**: Python 3.12+
- **Plugin framework**: `dify_plugin` (>=0.4.2, <0.5.0)
- **Apify SDK**: `apify-client`
- **HTTP utilities**: `requests`, `werkzeug`
- **Linting**: `flake8`, `ruff` (line length 120, target py312)
- **Package manager**: `uv`

## Build, Test & Run

```bash
# Install dependencies
uv pip install -r requirements.txt

# Lint
flake8 .

# Validate plugin packaging (requires Dify Plugin CLI)
dify plugin package .

# Debug locally (set REMOTE_INSTALL_KEY in .env)
cp .env.example .env
python main.py
```

### CI

- **PRs to main**: lint + plugin validation (`test.yml`)
- **Version tags (`v*`)**: lint, validate, package, publish GitHub release with `.difypkg` artifact (`release.yml`)

## Conventions

- **Python style**: Ruff formatter, line length 120, target Python 3.12
- **Commit format**: conventional commits (`fix:`, `ci:`, `feat:`, etc.)
- **Branching**: feature branches → PR to `main`
- **Versioning**: bump `manifest.yaml` version, then tag with `v<version>` to trigger release

## Key Notes for AI Assistants

- This is a **Python Dify plugin**, not a Node.js project. There is no `package.json`.
- The plugin does **not store or cache user data**; credentials are held by Dify and passed at runtime.
- Tool schemas live in `tools/*.yaml` and must stay in sync with the corresponding `tools/*.py` implementations.
- `manifest.yaml` controls plugin version, minimum Dify version (`1.11.4`), memory (`256MB`), and enabled permissions — update it when adding new tools or endpoints.
- The `ANTHROPIC_API_KEY` secret used by `claude-md-maintenance.yml` is stored as `CLAUDE_MD_MAINTENANCE_ANTHROPIC_API_KEY` in the repo secrets and is managed by the Apify integrations team.
