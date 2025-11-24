# TickTick API Examples & Authentication Guide

This document provides a complete guide to authenticating with the TickTick API and using `curl` to perform common operations.

## 1. One-Time Setup on TickTick Developer Portal

Before using the API, you must register an application with TickTick.

1.  Navigate to [developer.ticktick.com](https://developer.ticktick.com/) and sign in.
2.  Click on **Manage Apps** in the top navigation bar.
3.  Click **"Create an app"** or edit an existing application.
4.  On your application's page, you will find the **"Client ID"** and **"Client Secret"**. You will need these for your `.env` file.
5.  Set the **"OAuth redirect URL"** to the following exact value:
    ```
    http://localhost:8080
    ```
    This is crucial for the authentication script to work correctly.

## 2. Local Environment Setup

Your local project directory should contain the following files:

*   `.env`: To store your credentials.
*   `get_token.py`: The script to get your access token.
*   `requirements.txt`: The dependencies for the Python script.

### The `.env` File

Create a file named `.env` and populate it with the "Client ID" and "Client Secret" from the TickTick developer portal:

```
# .env
TICKTICK_CLIENT_ID=your_client_id_from_ticktick
TICKTICK_CLIENT_SECRET=your_client_secret_from_ticktick
```

### Install Dependencies

Install the Python libraries required by the authentication script:

```bash
pip install -r requirements.txt
```

## 3. Getting Your Access Token

The TickTick API uses OAuth 2.0, which requires user authorization to grant access. The included `get_token.py` script automates this process.

### How it Works

When you run the script, it will:
1.  Start a temporary web server on your local machine.
2.  Open your default web browser to a TickTick authorization page.
3.  You must log in to your TickTick account (if you aren't already) and click **"Allow"** on the consent page to grant your application access.
4.  After you click "Allow," TickTick redirects your browser back to the script's local web server. The URL of this redirect will contain a temporary `code` (e.g., `http://localhost:8080/?code=hgbZDt...`).
5.  The script automatically captures this `code`, shuts down the local server, and exchanges the `code` for an `access_token`.
6.  Finally, the script automatically adds or updates the `TICKTICK_ACCESS_TOKEN` in your `.env` file.

### Running the Script

To get your initial token or to get a new one after the old one expires, run the following command:

```bash
python3 get_token.py
```

Follow the prompts in your browser. Upon completion, your `.env` file will be updated with a valid access token.

---

## 4. Manual API Calls with `curl`

Once you have a valid access token, you can use it to make direct API calls with `curl`.

### Loading Environment Variables

Before running the `curl` commands, load the variables from your `.env` file into your shell session:

```bash
export $(cat .env | xargs)
```

### Example API Calls

*(Note: These examples will be filled in once a valid access token is confirmed and the API endpoints are successfully tested.)*

#### List all Projects
```bash
# To be filled in...
```

#### List Tasks (up to 50)
```bash
# To be filled in...
```

#### Add a Dummy Task
```bash
# To be filled in...
```

#### Mark a Task as Complete
```bash
# To be filled in...
```

#### Delete a Task
```bash
# To be filled in...
```