"""OAuth 2.0 helper to obtain a TickTick access token.

Used by the ``ticktick auth login`` CLI command. The resulting token
is meant to be fed into ``ticktick-admin users add`` /
``ticktick-admin users update-profile`` so it lives in the
mcp-app user store, not in any local config file.
"""

from __future__ import annotations

import http.server
import socketserver
import webbrowser
from urllib.parse import parse_qs, urlparse

import httpx

AUTH_URL = "https://ticktick.com/oauth/authorize"
TOKEN_URL = "https://ticktick.com/oauth/token"
REDIRECT_URI = "http://localhost:8080"
SCOPE = "tasks:read tasks:write"
STATE = "ticktick-access-oauth"
PORT = 8080


class _CallbackHandler(http.server.SimpleHTTPRequestHandler):
    """Captures the authorization code from the OAuth redirect."""

    authorization_code: str | None = None
    server_should_stop: bool = False

    def do_GET(self):  # noqa: N802 — http.server API
        params = parse_qs(urlparse(self.path).query)
        if "code" in params:
            _CallbackHandler.authorization_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"<html><body style='font-family:sans-serif;text-align:center;'>"
                b"<h1>Authentication Successful</h1>"
                b"<p>Return to the terminal - your access token is being printed there.</p>"
                b"</body></html>"
            )
        else:
            self.send_response(400)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>Authentication Failed</h1>")
        _CallbackHandler.server_should_stop = True

    def log_message(self, format, *args):  # noqa: A002 — http.server API
        return


def run_oauth_flow(client_id: str, client_secret: str) -> str:
    """Open the browser for OAuth authorization and return the access token.

    Raises:
        RuntimeError: If the user cancels or no code is returned.
        httpx.HTTPError: If the token-exchange request fails.
    """
    _CallbackHandler.authorization_code = None
    _CallbackHandler.server_should_stop = False

    with socketserver.TCPServer(("", PORT), _CallbackHandler) as httpd:
        url = (
            f"{AUTH_URL}?client_id={client_id}&scope={SCOPE}"
            f"&redirect_uri={REDIRECT_URI}&state={STATE}&response_type=code"
        )
        print(f"Opening browser for TickTick authorization on port {PORT}.")
        print(f"If your browser doesn't open, visit: {url}")
        webbrowser.open(url)

        while not _CallbackHandler.server_should_stop:
            httpd.handle_request()

    if not _CallbackHandler.authorization_code:
        raise RuntimeError("Authorization cancelled or no code returned.")

    response = httpx.post(
        TOKEN_URL,
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": _CallbackHandler.authorization_code,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
            "scope": SCOPE,
        },
        timeout=30,
    )
    response.raise_for_status()
    body = response.json()
    token = body.get("access_token")
    if not token:
        raise RuntimeError(f"No access_token in TickTick response: {body}")
    return token
