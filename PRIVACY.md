# Privacy Policy for Apify Plugin

This document describes how the Apify plugin for Dify handles user data.

## Data Handling

The Apify plugin for Dify acts as a pass-through service. It directly communicates with the official Apify API to perform its functions. **This plugin does not store, cache, or log any user data or credentials on any third-party servers.**

## Authentication

User authentication credentials (OAuth tokens or API Tokens) are handled exclusively by the Dify platform. These credentials are encrypted and stored securely by Dify. The plugin code accesses these credentials at runtime to make authenticated API calls to Apify on your behalf but does not export or expose them.

## Third-Party Services

All data processing, actor execution, and data storage occur on the Apify platform. The Web Fetch tool sends the URL and any custom headers you provide to the Web Fetch Actor on the Apify platform, which forwards those headers to the target URL when fetching it. Your use of this plugin is subject to the [Apify Terms of Service](https://docs.apify.com/legal/general-terms-and-conditions) and [Privacy Policy](https://docs.apify.com/legal/privacy-policy).