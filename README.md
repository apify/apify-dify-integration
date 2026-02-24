# Apify Integration for Dify

This repository contains a plugin for the [Dify.ai](https://dify.ai/) platform, enabling seamless integration with the [Apify](https://apify.com/) web scraping and automation platform.

## Features
- **Run Actor** – Start any Apify actor by its unique `actorId` with custom input.  
- **Run Task** – Execute predefined Apify tasks with one click.  
- **Scrape Single URL** – Quickly scrape data from a single web page without configuring a full crawl.  
- **Get Dataset Items** – Retrieve results stored in an Apify dataset.  
- **Get Key-Value Store Record** – Fetch a record from an Apify key-value store.  
- **Actor Run Finished Trigger** – Trigger downstream actions in Dify when an Apify actor or task run finishes.  
- **Flexible Execution Modes** – Choose between asynchronous (fast return) and synchronous (wait for results) execution.
- **Finished Trigger (Webhook)** – Trigger Dify workflows automatically upon the completion of an Apify Actor or task.

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

## Usage Example: Running an Actor

This section shows how to run an Apify actor inside a Dify workflow.  
We will use the **Google Maps Scraper** actor (`compass/crawler-google-places`) as an example.

### Step 1: Create a New Workflow
1. Open your **Dify project**.
2. Create a new **Workflow** from Blank.
3. Click on the **+** button followed by **Tools -> Apify -> Run Actor**.

<img 
  src="https://raw.githubusercontent.com/apify/apify-dify-integration/main/docs/images/dify-workflow-start.png" 
  alt="Start Dify Workflow"
/>

4. Fill in the following settings:
   - **Actor ID**: `compass/crawler-google-places`
   - **Input**:  
     ```json
     {
       "language": "en",
       "locationQuery": "New York, USA",
       "maxCrawledPlacesPerSearch": 50,
       "placeMinimumStars": "two",
       "searchStringsArray": ["restaurant"],
       "skipClosedPlaces": false
     }
     ```
   - **Wait for Finish**:  
    Set to `false` if you want the workflow to return immediately after starting or to `true` if you want to wait for the run to reach a terminal state (e.g SUCCEEDED, FAILED).

<img 
  src="https://raw.githubusercontent.com/apify/apify-dify-integration/main/docs/images/dify-configure-actor-run.png" 
  alt="Configure Actor Run" 
/>

### Step 3: Connect Workflow Blocks
1. Select **Output** block in a workflow.
2. Connect the **Run Actor** block to the **Output** block.  
3. Create a variable to store results:
    - Open the output of the **Output** block.  
    - Add a variable, e.g., `result`, that maps to the actor’s response.  

<img 
  src="https://raw.githubusercontent.com/apify/apify-dify-integration/main/docs/images/dify-configure-end-node.png" 
  alt="Configure End Node" 
/>

### Step 4: Run the Workflow
1. Click the **Run** button.  
2. Dify will trigger the Apify actor.  
3. Run details (including run ID) are returned immediately or after completion, depending on `Wait for Finish` parameter.
4. You can check results in [Apify Console Runs Page](https://console.apify.com/actors/runs).

## Support
- For Apify documentation, visit [docs.apify.com](https://docs.apify.com).  
- For Dify plugin development, check [Dify Plugin Docs](https://docs.dify.ai/plugin-dev-en/).  
