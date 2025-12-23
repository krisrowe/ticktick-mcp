import http.server
import os
import socketserver
import webbrowser
from urllib.parse import parse_qs, urlparse

import requests

# --- Configuration ---
# This script assumes you have a .env file in the same directory with:
# TICKTICK_CLIENT_ID=your_client_id
# TICKTICK_CLIENT_SECRET=your_client_secret

# Try to load from .env file. If python-dotenv is not installed, it will fail gracefully.
try:
    from dotenv import load_dotenv

    load_dotenv()
    print("Loaded credentials from .env file.")
except ImportError:
    print("Warning: python-dotenv is not installed. Trying to read from environment variables directly.")
    print("You can install it with: pip install python-dotenv")


CLIENT_ID = os.getenv("TICKTICK_CLIENT_ID")
CLIENT_SECRET = os.getenv("TICKTICK_CLIENT_SECRET")
# The redirect URI must exactly match the one registered in your TickTick app settings.
# We will listen on port 8080.
REDIRECT_URI = "http://localhost:8080"
AUTH_URL = "https://ticktick.com/oauth/authorize"
TOKEN_URL = "https://ticktick.com/oauth/token"
SCOPE = "tasks:read tasks:write"
# In a real app, this should be a securely generated random string.
STATE = "random-string-for-security"
PORT = 8080

# This global variable will be used to pass the authorization code from the server handler to the main script.
authorization_code = None
server_is_running = True


class OAuthCallbackHandler(http.server.SimpleHTTPRequestHandler):
    """
    A simple HTTP request handler that captures the OAuth 'code' from the redirect.
    """

    def do_GET(self):
        global authorization_code, server_is_running

        # Parse the query parameters from the request URL
        query_components = parse_qs(urlparse(self.path).query)

        if "code" in query_components:
            authorization_code = query_components["code"][0]
            # Send a success response to the browser
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><head><title>Authentication Successful</title></head>")
            self.wfile.write(b"<body style='font-family: sans-serif; text-align: center;'>")
            self.wfile.write(b"<h1>Authentication Successful!</h1>")
            self.wfile.write(b"<p>You can now close this browser window and return to the terminal.</p>")
            self.wfile.write(b"</body></html>")
        else:
            # Handle the case where the 'code' is not in the query parameters
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>Authentication Failed</h1>")
            self.wfile.write(b"<p>Could not find an authorization code in the request. Please try again.</p>")

        # Signal the server to stop
        server_is_running = False


def get_new_access_token():
    """
    Orchestrates the OAuth 2.0 Authorization Code Grant flow.
    """
    global server_is_running, authorization_code

    with socketserver.TCPServer(("", PORT), OAuthCallbackHandler) as httpd:
        print(f"Temporarily starting a local web server on port {PORT}...")

        # 1. Construct the authorization URL and open it in the user's browser.
        auth_request_url = f"{AUTH_URL}?client_id={CLIENT_ID}&scope={SCOPE}&redirect_uri={REDIRECT_URI}&state={STATE}&response_type=code"

        print("\nYour browser should now open for you to authorize the application.")
        print("If it doesn't, please open this URL manually:")
        print(f"-> {auth_request_url}")

        webbrowser.open(auth_request_url)

        # 2. Wait for the server to handle the redirect and capture the code.
        while server_is_running:
            httpd.handle_request()

    if not authorization_code:
        print("\nCould not retrieve an authorization code. The process was likely cancelled.")
        return

    print("\nSuccessfully received an authorization code.")

    # 3. Exchange the authorization code for an access token.
    print("Exchanging the authorization code for an access token...")

    token_payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": authorization_code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPE,
    }

    try:
        response = requests.post(TOKEN_URL, data=token_payload)
        response.raise_for_status()  # This will raise an exception for HTTP errors
    except requests.exceptions.RequestException as e:
        print(f"\nError requesting access token: {e}")
        return

    token_info = response.json()
    access_token = token_info.get("access_token")

    if not access_token:
        print("\nFailed to get access token. The response did not contain one.")
        print("Response:", token_info)
        return

    print("\n--- ✨ New Access Token Received! ✨ ---")
    print(f"Access Token: {access_token}")
    print("---------------------------------------\n")

    # 4. Update the .env file with the new token.
    print("Updating .env file with the new access token...")
    env_file_path = ".env"

    # Read the existing .env file, filtering out the old access token
    try:
        with open(env_file_path) as f:
            lines = [line for line in f.readlines() if not line.strip().startswith("TICKTICK_ACCESS_TOKEN")]
    except FileNotFoundError:
        lines = []

    # Write back the filtered lines plus the new access token
    with open(env_file_path, "w") as f:
        f.writelines(lines)
        f.write(f"TICKTICK_ACCESS_TOKEN={access_token}\n")

    print(f"Successfully updated '{env_file_path}'. You can now use this token for API calls.")


if __name__ == "__main__":
    if not CLIENT_ID or not CLIENT_SECRET:
        print(
            "🔴 Error: 'TICKTICK_CLIENT_ID' and 'TICKTICK_CLIENT_SECRET' must be set in a .env file or as environment variables."
        )
    else:
        get_new_access_token()
