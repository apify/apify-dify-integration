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
uv pip install -e ".[dev]"
```

**8. Install Dependencies**

This project uses a `requirements.txt` file to manage its dependencies.

```bash
pip install -r requirements.txt
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
  
     <img width="266" height="223" alt="image" src="https://github.com/user-attachments/assets/e592712d-a741-45c7-96ef-66231e201262" />

3. **Run the project**  
   Start the project in debug mode with:  
    ```bash
    python -m main
    ```

## Usage Example: Running an Actor

This section shows how to run an Apify actor inside a Dify workflow.  
We will use the **Google Maps Extractor** actor (`2Mdma1N6Fd0y3QEjR`) as an example.

### Step 1: Create a New Workflow
1. Open your **Dify project**.
2. Create a new **Workflow** from Blank.

<img width="978" height="435" alt="image" src="https://github.com/user-attachments/assets/d913230f-11bf-42e3-a68a-bb80a549daf3" />
<img width="704" height="546" alt="image" src="https://github.com/user-attachments/assets/ffcd6bf6-4831-48b7-a630-2ce38c57803f" />

4. Drag and drop the **Run Actor (Apify Plugin)** block onto the canvas.

<img width="891" height="469" alt="image" src="https://github.com/user-attachments/assets/a8b0c545-5e2f-4845-ab72-36f230134906" />

### Step 2: Configure the Run Actor Block
1. Select the **Run Actor** block.  
2. Fill in the following settings:
   - **Actor ID**:  
     ```
     2Mdma1N6Fd0y3QEjR
     ```
   - **Example Input Body** (JSON):  
     ```json
     {
       "categoryFilterWords": ["abbey"],
       "countryCode": "af",
       "language": "en",
       "locationQuery": "New York, USA",
       "maxCrawledPlacesPerSearch": 1,
       "placeMinimumStars": "two",
       "searchMatching": "all",
       "searchStringsArray": ["restaurant"],
       "skipClosedPlaces": false,
       "website": "allPlaces"
     }
     ```
   - **Wait for Finish**:  
   Set to `false` (the workflow will return immediately without waiting for the actor to complete).  

<img width="1288" height="710" alt="image" src="https://github.com/user-attachments/assets/585f6eec-d06d-4e65-8da4-334abfa2eff7" />

### Step 3: Connect Workflow Blocks
1. Put **End** block in a workflow.

<img width="1013" height="229" alt="image" src="https://github.com/user-attachments/assets/ad0cf992-50ae-4ffb-953e-d16edf445a56" />

2. Connect the **Run Actor** block to the **End** block.  
3. Create a variable to store results:  
   - Open the output of the **End** block.  
   - Add a variable, e.g., `result`, that maps to the actor’s response.  

<img width="931" height="401" alt="image" src="https://github.com/user-attachments/assets/c6ca7068-d980-4f92-8d38-e1374f008eac" />

### Step 4: Run the Workflow
1. Click the **Run** button.  
2. Dify will trigger the Apify actor `2Mdma1N6Fd0y3QEjR`.  
3. Since `wait_for_finish = false`, the workflow will immediately return with the run details (including the run ID).  
4. You can check results in [Apify Console Runs Page](https://console.apify.com/actors/runs).

## Support
- For Apify documentation, visit [docs.apify.com](https://docs.apify.com).  
- For Dify plugin development, check [Dify Plugin Docs](https://docs.dify.ai/plugin-dev-en/).  
