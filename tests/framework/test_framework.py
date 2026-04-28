"""mcp-app framework conformance tests against the ticktick App.

This file is identical for every mcp-app solution. The conformance
suite ships with mcp-app and runs against YOUR App via the fixture
in conftest.py.
"""

from mcp_app.testing.iam.test_admin_errors import *  # noqa: F401, F403
from mcp_app.testing.iam.test_admin_local import *  # noqa: F401, F403
from mcp_app.testing.iam.test_auth_enforcement import *  # noqa: F401, F403
from mcp_app.testing.wiring.test_app_wiring import *  # noqa: F401, F403
from mcp_app.testing.tools.test_sdk_coverage_audit import *  # noqa: F401, F403
from mcp_app.testing.health.test_health import *  # noqa: F401, F403
