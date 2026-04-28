"""Tests for the ticktick OAuth-helper CLI.

In-process CliRunner — no subprocesses. The OAuth network call is the
only mocked boundary; the rest of the CLI machinery (Click parsing,
output formatting, error paths) runs for real.
"""

from unittest.mock import patch

from click.testing import CliRunner

from ticktick.cli import cli


def test_cli_shows_version():
    result = CliRunner().invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "ticktick" in result.output


def test_auth_login_requires_client_id_and_secret():
    """No env vars, no flags — Click rejects before doing any network I/O."""
    result = CliRunner().invoke(
        cli, ["auth", "login"],
        env={"TICKTICK_CLIENT_ID": "", "TICKTICK_CLIENT_SECRET": ""},
    )
    assert result.exit_code != 0
    assert "client" in result.output.lower() or "missing" in result.output.lower()


def test_auth_login_prints_token_on_success():
    with patch("ticktick.cli.run_oauth_flow", return_value="freshly-minted-token"):
        result = CliRunner().invoke(
            cli, [
                "auth", "login",
                "--client-id", "cid",
                "--client-secret", "csecret",
            ],
        )
    assert result.exit_code == 0
    assert "freshly-minted-token" in result.output


def test_auth_login_reports_error_on_failure():
    with patch("ticktick.cli.run_oauth_flow", side_effect=RuntimeError("boom")):
        result = CliRunner().invoke(
            cli, [
                "auth", "login",
                "--client-id", "cid",
                "--client-secret", "csecret",
            ],
        )
    assert result.exit_code != 0
    assert "boom" in result.output


def test_auth_login_reads_credentials_from_env():
    """Operators can avoid putting secrets on the command line."""
    with patch("ticktick.cli.run_oauth_flow", return_value="env-token") as mock_flow:
        result = CliRunner().invoke(
            cli, ["auth", "login"],
            env={"TICKTICK_CLIENT_ID": "envcid", "TICKTICK_CLIENT_SECRET": "envsec"},
        )
    assert result.exit_code == 0, result.output
    mock_flow.assert_called_once_with("envcid", "envsec")
