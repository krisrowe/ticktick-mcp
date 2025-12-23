"""OAuth 2.0 authentication flow for TickTick API."""

import http.server
import socketserver
import webbrowser
from urllib.parse import parse_qs, urlparse

import requests

from .config import save_token

# TickTick OAuth endpoints
AUTH_URL = "https://ticktick.com/oauth/authorize"
TOKEN_URL = "https://ticktick.com/oauth/token"
REDIRECT_URI = "http://localhost:8080"
SCOPE = "tasks:read tasks:write"
STATE = "ticktick-access-oauth"
PORT = 8080


class OAuthCallbackHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler that captures OAuth authorization code from redirect."""

    authorization_code: str | None = None
    server_should_stop: bool = False

    def do_GET(self):
        """Handle GET request from OAuth redirect."""
        query_components = parse_qs(urlparse(self.path).query)

        if "code" in query_components:
            OAuthCallbackHandler.authorization_code = query_components["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><head><title>Authentication Successful</title></head>")
            self.wfile.write(b"<body style='font-family: sans-serif; text-align: center;'>")
            self.wfile.write(b"<h1>Authentication Successful!</h1>")
            self.wfile.write(b"<p>You can now close this browser window and return to the terminal.</p>")
            self.wfile.write(b"</body></html>")
        else:
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>Authentication Failed</h1>")
            self.wfile.write(b"<p>Could not find an authorization code in the request. Please try again.</p>")

        OAuthCallbackHandler.server_should_stop = True

    def log_message(self, format, *args):
        """Suppress HTTP request logging."""
        pass


def run_oauth_flow(client_id: str, client_secret: str) -> str:
    """Run the OAuth 2.0 authorization code flow.

    Opens a browser for user authorization, captures the authorization code,
    and exchanges it for an access token.

    Args:
        client_id: TickTick OAuth client ID.
        client_secret: TickTick OAuth client secret.

    Returns:
        The access token.

    Raises:
        RuntimeError: If authorization fails or is cancelled.
        requests.RequestException: If token exchange fails.
    """
    # Reset handler state
    OAuthCallbackHandler.authorization_code = None
    OAuthCallbackHandler.server_should_stop = False

    with socketserver.TCPServer(("", PORT), OAuthCallbackHandler) as httpd:
        # Construct authorization URL
        auth_request_url = (
            f"{AUTH_URL}?client_id={client_id}&scope={SCOPE}"
            f"&redirect_uri={REDIRECT_URI}&state={STATE}&response_type=code"
        )

        print(f"\nStarting local server on port {PORT}...")
        print("\nYour browser should open for authorization.")
        print("If it doesn't, please open this URL manually:")
        print(f"  {auth_request_url}\n")

        webbrowser.open(auth_request_url)

        # Wait for callback
        while not OAuthCallbackHandler.server_should_stop:
            httpd.handle_request()

    if not OAuthCallbackHandler.authorization_code:
        raise RuntimeError("Authorization failed or was cancelled.")

    print("Authorization code received. Exchanging for access token...")

    # Exchange code for token
    token_payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": OAuthCallbackHandler.authorization_code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPE,
    }

    response = requests.post(TOKEN_URL, data=token_payload, timeout=30)
    response.raise_for_status()

    token_info = response.json()
    access_token = token_info.get("access_token")

    if not access_token:
        raise RuntimeError(f"No access token in response: {token_info}")

    # Save token to config
    save_token(access_token)
    print(f"\nAccess token saved to ~/.ticktick-access/token")

    return access_token
