# Apify Integration for Dify

Connect [Apify](https://apify.com/) with [Dify](https://dify.ai/) to run Actors, extract structured data, and trigger workflows when Actor or task runs finish.

## Features

- **Run Actor** – Start any Apify actor by its unique `actorId` with custom input.
- **Run Task** – Execute predefined Apify tasks with one click.
- **Scrape Single URL** – Quickly scrape data from a single web page without configuring a full crawl.
- **Get Dataset Items** – Retrieve results stored in an Apify dataset.
- **Get Key-Value Store Record** – Fetch a record from an Apify key-value store.
- **Actor Run Finished Trigger** – Trigger Dify workflows or chatflows when an Apify actor or task run completes (via webhook).
- **Flexible Execution Modes** – Choose between asynchronous (fast return) and synchronous (wait for results) execution.

## Prerequisites

Before you begin, make sure you have:

- An [Apify account](https://console.apify.com/)
- A [Dify account](https://dify.ai/) (self-hosted or cloud)

## Installation

1. In Dify, go to **Plugins** from the top menu.
2. Select **Install plugin** → **Marketplace**.
3. Find the **apify-integration** plugin and install it.
4. Return to the **Plugins** page to configure it.

## Authentication

To connect your Apify account, configure the plugin using your Apify API token or OAuth.

### API key

1. Open the plugin and select **Add API Key**.
2. Paste your Apify API token. You can find it in the [Apify Console](https://console.apify.com/account/integrations) under **Integrations**.
3. Select **Save**.

A green indicator confirms that your credentials are correct.

### OAuth

1. Open the plugin and select **Add OAuth**.
2. Follow the OAuth flow to authorize Dify to access your Apify account.
3. Select **Save** to complete the connection.

With authentication set up, you can add Apify tools to your workflows and applications.

## Usage Example: Running an Actor

This example shows how to run an Apify actor inside a Dify workflow using the **Google Maps Scraper** actor (`compass/crawler-google-places`).

### Step 1: Create a new workflow

1. Open your **Dify project** and create a new **Workflow** from Blank.
2. Click the **+** button, then **Tools** → **Apify** → **Run Actor**.

![Start Dify Workflow](https://raw.githubusercontent.com/apify/apify-dify-integration/main/docs/images/dify-workflow-start.png)

### Step 2: Configure the Run Actor node

1. Set **Actor ID** to `compass/crawler-google-places`.
2. Set **Input** to a JSON object, for example:

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

3. Set **Wait for Finish** to `false` to return immediately after starting the run, or `true` to wait until the run reaches a terminal state (e.g. SUCCEEDED, FAILED).

![Configure Actor Run](https://raw.githubusercontent.com/apify/apify-dify-integration/main/docs/images/dify-configure-actor-run.png)

### Step 3: Connect and configure the output

1. Add an **Output** node and connect the **Run Actor** node to it.
2. In the Output node, add a variable (e.g. `result`) and map it to the Run Actor response.

![Configure End Node](https://raw.githubusercontent.com/apify/apify-dify-integration/main/docs/images/dify-configure-end-node.png)

### Step 4: Run the workflow

1. Click **Run**.
2. Dify triggers the Apify actor. Run details (including run ID) are returned immediately or after completion, depending on **Wait for Finish**.
3. You can inspect runs and results in the [Apify Console](https://console.apify.com/actors/runs).

## Use Apify as a trigger

You can trigger Dify workflows or chatflows when an Apify actor or task run finishes.

1. In **Plugins**, open the Apify plugin and go to the **Endpoints** section.
2. Click **+** to create an endpoint, choose your **Workflow** or **Chatflow** app, and give it a name. Save. Dify generates trigger URLs.
3. In the [Apify Console](https://console.apify.com/), open your Actor, go to **Integrations**, add an **HTTP webhook**, and paste the Dify endpoint URL. Under **Events**, select **Run succeeded** and save.

Your Dify app must be **published** for the webhook to work. For more detail, including how to use webhook data (e.g. dataset ID) in your workflow, see the [Apify Dify integration guide](https://docs.apify.com/platform/integrations/dify).

## Support

- **Apify documentation**: [docs.apify.com](https://docs.apify.com)
- **Dify documentation**: [Dify documentation](https://docs.dify.ai/)
