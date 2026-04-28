"""Provides the App fixture for mcp-app's reusable test suite.

This file is the only piece that varies per app. tests/framework/
test_framework.py is identical across every mcp-app solution.
"""

import pytest

from ticktick import app as my_app


@pytest.fixture(scope="session")
def app():
    return my_app
