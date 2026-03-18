# Contributing to Apify Integration for Dify

This guide is for developers and contributors who want to set up the project locally, debug, or publish a new version.

## Prerequisites

Before you begin, ensure you have the following installed and configured:

  * **Python**: Version `3.12` or newer is required.
  * **UV**: You also need pre-installed [UV package manager](https://docs.astral.sh/uv/getting-started/installation/#standalone-installer) for Python
  * **Apify Account**: You will need an Apify account and your personal API Token. You can find your token in the [Apify Console](https://console.apify.com/account/integrations).
  * **Dify Account**: A Dify account to test the plugin.

## Installation & Setup

Follow these steps to set up the project for local development.

**1. Install with Standalone Binary (macOS / Linux)**

Download the right binary from the Dify Plugin CLI release [page](https://github.com/langgenius/dify-plugin-daemon/releases).

* macOS (ARM — Apple Silicon): e.g. `dify-plugin-darwin-arm64`
* macOS (Intel): `dify-plugin-darwin-amd64`
* Linux (amd64 or arm64): `dify-plugin-linux-amd64`

**2. Make the binary executable:**
```bash
chmod +x dify-plugin-<platform-arch>
```

**3. Run version check:**

```bash
./dify-plugin-<platform-arch> version
```

**4. Rename and move it to your system PATH:**
```bash
mv dify-plugin-<platform-arch> dify
sudo mv dify /usr/local/bin/
```

**5. Confirm installation with:**

```bash
dify version
```

**6. Clone the Repository**

```bash
git clone https://github.com/apify/apify-dify-integration.git
cd apify-dify-integration
```

**7. Create and Activate a Virtual Environment**

It is highly recommended to use a virtual environment to manage project dependencies.

```bash
# Create the virtual environment
uv venv

# Activate it (on macOS/Linux)
source .venv/bin/activate

# Install dependencies
uv pip install -e ".[dev]"
```

And we are pretty much ready!

## Lint and validate

Before pushing, run:

```bash
flake8 .
dify plugin package .
```

## Debugging & Development

To enable interactive debugging, follow these steps:

1. **Create an environment file**  
   Copy `.env.example` to `.env`.

2. **Obtain your debugging key**  
   - Go to the [Dify Plugins](https://cloud.dify.ai/plugins) page.  
   - Click the **bug icon** in the upper right corner to generate a debugging key.  
   - Replace the default value of `REMOTE_INSTALL_KEY` in your `.env` file with this key.
  
3. **Run the project**  
   Start the project in debug mode with:  
    ```bash
    python -m main
    ```

### Local debugging with Docker

To test the plugin against a local Dify instance, use [Docker Compose](https://docs.dify.ai/en/self-host/quick-start/docker-compose): clone Dify, start it with `docker compose up -d` from the `docker` directory, then complete the admin setup at `http://localhost/install`.

Build the plugin package and upload it in Dify to test:

```bash
# From the plugin repo root
dify plugin package . -o apify.difypkg
```

Then in your local Dify plugins page, upload the `apify.difypkg` local package file to install the plugin and test your changes.

## Contribution guidelines

Use feature branches and open a Pull Request to `main`. Before submitting, run `flake8 .` and `dify plugin package .` (CI runs these on PRs as well). Follow conventional commits (`feat:`, `fix:`, `ci:`, `docs:`, etc.) and keep `tools/*.yaml` in sync with `tools/*.py`. Update `manifest.yaml` when adding new tools or endpoints.

## Publishing a New Version to the Dify Marketplace

These steps are for maintainers releasing a new version to the Dify marketplace. Follow them when you want to release an updated version of the plugin.

**1. Update the version number**

In `manifest.yaml`, bump the `version` field following [semantic versioning](https://semver.org/):

```yaml
version: "0.0.2"  # was 0.0.1
```

Commit and push the change to `main`.

**2. Create a GitHub Release**

1. Go to the repository on GitHub → **Releases** → **Draft a new release**.
2. Click **Choose a tag** → type the new version (e.g. `v0.0.2`) → select **Create new tag: v0.0.2 on publish**.
3. Set the release title (e.g. `v0.0.2`).
4. Click **Publish release**.

This triggers the release workflow, which lints the code, packages the plugin, and attaches `apify.difypkg` to the release assets.

**3. Download the `.difypkg` file**

Once the workflow finishes (~1–2 min), go to the release page and download `apify.difypkg` from the **Assets** section. Rename it to include the version, e.g. `apify-0.0.2.difypkg`.

**4. Submit a PR to the Dify plugins repository**

1. Go to your fork of [langgenius/dify-plugins](https://github.com/langgenius/dify-plugins).
2. Navigate to `apify/apify-integration/`.
3. Upload `apify-0.0.2.difypkg` (keep previous version files — multiple versions can coexist).
4. Open a Pull Request to `langgenius/dify-plugins:main`.
5. In the PR description, select **Version update** as the submission type and briefly describe what changed.

After the PR is merged, the new version appears automatically on the Dify marketplace.

## Support

- For Apify documentation, visit [docs.apify.com](https://docs.apify.com).
- For Dify plugin development, check [Dify Plugin Docs](https://docs.dify.ai/plugin-dev-en/).
