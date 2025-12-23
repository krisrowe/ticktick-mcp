# Manual Integration Testing Guide

This guide covers manual integration testing of the TickTick MCP Server. While unit tests verify code logic with mocked requests, manual integration testing verifies that the server functions work correctly with real API calls.

## Quick Start: Simple Python Script (Recommended)

The easiest way to test integration is using the provided Python script that tests server functions directly (no HTTP/SSE complexity):

```bash
# Ensure virtual environment is activated and dependencies installed
source venv/bin/activate  # or: python3 -m venv venv && source venv/bin/activate
pip install -e ".[dev]"

# Ensure TICKTICK_ACCESS_TOKEN is set in .env or environment
source .env  # or export TICKTICK_ACCESS_TOKEN="your_token"

# Run the simple integration test script
python test_integration_simple.py
```

This script tests:
- ✅ Getting list of projects
- ✅ Getting list of tasks in a project
- ✅ Getting details of a task
- ✅ (Optional) Updating a task

**Advantages:**
- No Docker required
- No HTTP/SSE complexity
- Direct function testing
- Clear, readable output
- Fast execution

## Alternative: Docker + curl Testing (Advanced)

For testing the full Docker container with HTTP endpoints, see the sections below. Note that the MCP server uses Server-Sent Events (SSE), which makes curl testing more complex.

## Prerequisites

1. **Docker image built and running:**
   ```bash
   # Build the image
   docker build -t ticktick-mcp-server:latest .
   
   # Run the container (ensure TICKTICK_ACCESS_TOKEN is set)
   source .env
   docker run -d \
     --name ticktick-mcp-server \
     -p 8000:8000 \
     -e TICKTICK_ACCESS_TOKEN="$TICKTICK_ACCESS_TOKEN" \
     ticktick-mcp-server:latest
   ```

2. **Valid `TICKTICK_ACCESS_TOKEN`** in your `.env` file (obtain via `python get_token.py`)

3. **Optional but recommended:** Install `jq` for pretty JSON output:
   ```bash
   # Linux
   sudo apt-get install jq
   
   # macOS
   brew install jq
   ```

## Testing Workflow

### Step 1: Initialize MCP Connection

```bash
curl -s http://localhost:8000/mcp -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {
        "name": "integration-test",
        "version": "1.0"
      }
    }
  }' | jq .
```

**Expected:** JSON response with `"result"` containing server capabilities and tool/resource lists.

### Step 2: List Available Tools

```bash
curl -s http://localhost:8000/mcp -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list"
  }' | jq '.result.tools[] | {name: .name, description: .description}'
```

**Expected:** List of available tools including `list_projects`, `list_tasks`, `create_task`, `update_task`, `complete_task`.

### Step 3: Test `list_projects` Tool

```bash
curl -s http://localhost:8000/mcp -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "list_projects",
      "arguments": {}
    }
  }' | jq '.result.content[0].text | fromjson'
```

**Expected:** JSON object with `projects` array and `count` field. Each project should have `id`, `name`, and other metadata.

**Verification:**
- ✅ Response contains `projects` array
- ✅ Response contains `count` field matching array length
- ✅ Each project has an `id` field (needed for other operations)
- ✅ No error messages in response

### Step 4: Test `list_tasks` Tool

First, get a project ID from Step 3, then:

```bash
# Replace PROJECT_ID_HERE with an actual project ID from Step 3
PROJECT_ID="PROJECT_ID_HERE"

curl -s http://localhost:8000/mcp -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d "{
    \"jsonrpc\": \"2.0\",
    \"id\": 4,
    \"method\": \"tools/call\",
    \"params\": {
      \"name\": \"list_tasks\",
      \"arguments\": {
        \"project_id\": \"$PROJECT_ID\"
      }
    }
  }" | jq '.result.content[0].text | fromjson'
```

**Expected:** JSON object with `project_id`, `tasks` array, `count`, `completed`, and `incomplete` fields.

**Verification:**
- ✅ Response contains `tasks` array
- ✅ Response contains `count`, `completed`, `incomplete` fields
- ✅ `project_id` matches the input parameter
- ✅ Each task has `id`, `title`, `status`, `projectId` fields
- ✅ Task counts are accurate (`completed + incomplete = count`)

### Step 5: Test Getting Task Details (via Resource)

```bash
# Use a task ID from Step 4
TASK_ID="TASK_ID_HERE"
PROJECT_ID="PROJECT_ID_HERE"

curl -s http://localhost:8000/mcp -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d "{
    \"jsonrpc\": \"2.0\",
    \"id\": 5,
    \"method\": \"resources/read\",
    \"params\": {
      \"uri\": \"ticktick://tasks/$PROJECT_ID\"
    }
  }" | jq '.result.contents[0].text | fromjson | .[0]'
```

**Expected:** JSON array of tasks, with the first task matching the expected structure.

### Step 6: Test `update_task` Tool

```bash
# Use real task_id and project_id from previous steps
TASK_ID="TASK_ID_HERE"
PROJECT_ID="PROJECT_ID_HERE"

curl -s http://localhost:8000/mcp -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d "{
    \"jsonrpc\": \"2.0\",
    \"id\": 6,
    \"method\": \"tools/call\",
    \"params\": {
      \"name\": \"update_task\",
      \"arguments\": {
        \"task_id\": \"$TASK_ID\",
        \"project_id\": \"$PROJECT_ID\",
        \"title\": \"Updated Test Title\",
        \"priority\": 2
      }
    }
  }" | jq '.result.content[0].text | fromjson'
```

**Expected:** JSON object with `success: true`, `message`, and `task` object containing updated task data.

**Verification:**
- ✅ Response contains `success: true`
- ✅ Response contains updated `task` object
- ✅ Task `title` matches the update value
- ✅ Task `priority` matches the update value
- ✅ Other task fields are preserved (not lost)

### Step 7: Verify Update Persisted

Re-run Step 4 (`list_tasks`) and verify the task was actually updated in TickTick:

```bash
curl -s http://localhost:8000/mcp -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d "{
    \"jsonrpc\": \"2.0\",
    \"id\": 7,
    \"method\": \"tools/call\",
    \"params\": {
      \"name\": \"list_tasks\",
      \"arguments\": {
        \"project_id\": \"$PROJECT_ID\"
      }
    }
  }" | jq ".result.content[0].text | fromjson | .tasks[] | select(.id == \"$TASK_ID\")"
```

**Expected:** Task object showing the updated title and priority.

## Error Case Testing

### Test Invalid Project ID

```bash
curl -s http://localhost:8000/mcp -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 8,
    "method": "tools/call",
    "params": {
      "name": "list_tasks",
      "arguments": {
        "project_id": "INVALID_PROJECT_ID"
      }
    }
  }' | jq '.error, .result'
```

**Expected:** Either an error response or a result with empty `tasks` array and `count: 0`.

## Troubleshooting

### 401 Unauthorized errors
- Token may have expired. Re-run `python get_token.py` and restart the container.

### Connection refused
- Ensure container is running: `docker ps | grep ticktick-mcp-server`
- Check container logs: `docker logs ticktick-mcp-server`

### Empty or null responses
- Verify `TICKTICK_ACCESS_TOKEN` is set correctly in the container
- Check container logs for API errors
- Ensure you're using valid project/task IDs from your TickTick account

### jq not found
- Install jq: `sudo apt-get install jq` (Linux) or `brew install jq` (macOS)
- Or remove `| jq .` from commands to see raw JSON

## Quick Test Script

Save this as `test-integration.sh`:

```bash
#!/bin/bash
set -e

echo "Testing MCP Server Integration..."
echo ""

# Initialize
echo "1. Initializing MCP connection..."
curl -s http://localhost:8000/mcp -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | jq -r '.result.serverInfo.name // "ERROR"'
echo ""

# List projects
echo "2. Testing list_projects..."
PROJECTS=$(curl -s http://localhost:8000/mcp -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"list_projects","arguments":{}}}' | jq -r '.result.content[0].text | fromjson | .projects[0].id // "ERROR"')
echo "First project ID: $PROJECTS"
echo ""

if [ "$PROJECTS" != "ERROR" ] && [ -n "$PROJECTS" ]; then
  echo "3. Testing list_tasks for project $PROJECTS..."
  curl -s http://localhost:8000/mcp -X POST \
    -H "Content-Type: application/json" \
    -H "Accept: application/json" \
    -d "{\"jsonrpc\":\"2.0\",\"id\":3,\"method\":\"tools/call\",\"params\":{\"name\":\"list_tasks\",\"arguments\":{\"project_id\":\"$PROJECTS\"}}}}" | jq -r '.result.content[0].text | fromjson | "Tasks found: \(.count), Completed: \(.completed), Incomplete: \(.incomplete)"'
  echo ""
  echo "✅ Integration tests completed successfully!"
else
  echo "❌ Integration tests failed - could not retrieve projects"
  exit 1
fi
```

Make it executable and run:
```bash
chmod +x test-integration.sh
./test-integration.sh
```

## Test Coverage

This integration testing guide covers the following functional test cases:

- ✅ **Getting list of projects** - Step 3 (`list_projects` tool)
- ✅ **Getting list of tasks in a project** - Step 4 (`list_tasks` tool)
- ✅ **Getting details of a task** - Step 5 (via resource read)
- ✅ **Updating a task** - Step 6 (`update_task` tool) and Step 7 (verification)
- ✅ **Error handling** - Invalid project ID test case

These tests verify end-to-end functionality with real API calls, complementing the unit tests that use mocked HTTP requests.
