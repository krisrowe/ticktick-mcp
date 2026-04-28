.PHONY: install test framework-test clean uninstall help venv

# Auto-create venv on first invocation; idempotent thereafter.
venv:
	@if [ ! -d ".venv" ]; then \
		python3 -m venv .venv && \
		. .venv/bin/activate && pip install --upgrade pip && pip install -e '.[dev]'; \
	fi

install:
	@command -v pipx >/dev/null 2>&1 || (echo "pipx not found; install with: pip install pipx"; exit 1)
	@echo "Installing ticktick-access with pipx..."
	@pipx install -e . --force 2>/dev/null || pipx install . --force
	@echo "Done. CLIs installed: ticktick, ticktick-mcp, ticktick-admin"

test: venv
	@. .venv/bin/activate && pytest

framework-test: venv
	@. .venv/bin/activate && pytest tests/framework/ -v

clean:
	rm -rf .venv build/ dist/ *.egg-info/ .pytest_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

uninstall:
	pipx uninstall ticktick-access 2>/dev/null || true

help:
	@echo "Targets:"
	@echo "  install         - Install with pipx (CLI + MCP server + admin CLI)"
	@echo "  test            - Run unit + framework tests (auto-creates venv)"
	@echo "  framework-test  - Run only mcp-app framework conformance tests"
	@echo "  clean           - Remove venv and build artifacts"
	@echo "  uninstall       - Remove from pipx"
