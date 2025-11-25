# TickTick MCP Server Tools and Resources

This document describes all tools and resources exposed by the TickTick MCP Server for use by LLMs and MCP clients.

## Tools

Tools allow LLMs to perform actions and make changes to your TickTick account.

### `list_projects`

**Purpose:** Retrieve all TickTick projects (lists) available to the authenticated user.

**Input:** None

**Output:**
```json
{
  "projects": [
    {
      "id": "project_id_here",
      "name": "Project Name",
      ...
    }
  ],
  "count": 5
}
```

**Use Cases:**
- Discover available projects before creating tasks
- Find project IDs needed for other tools
- Get an overview of all your TickTick lists

---

### `list_tasks`

**Purpose:** Retrieve all tasks from a specific TickTick project/list.

**Input:**
- `project_id` (string, required): The ID of the project to retrieve tasks from

**Output:**
```json
{
  "project_id": "project_id_here",
  "tasks": [
    {
      "id": "task_id_here",
      "title": "Task Title",
      "status": 0,
      "priority": 0,
      "dueDate": "2024-12-31T23:59:59Z",
      ...
    }
  ],
  "count": 10,
  "completed": 3,
  "incomplete": 7
}
```

**Use Cases:**
- View all tasks in a project
- Find task IDs for completing or updating tasks
- Get task status and metadata

---

### `create_task`

**Purpose:** Create a new task in a TickTick project.

**Input:**
- `project_id` (string, required): The ID of the project where the task should be created
- `title` (string, required): The title/name of the task
- `content` (string, optional): Description or content for the task
- `priority` (integer, optional): Priority level from 0-5 (default: 0). Higher numbers = higher priority
- `due_date` (string, optional): Due date in ISO 8601 format (e.g., "2024-12-31T23:59:59Z")

**Output:**
```json
{
  "success": true,
  "task": {
    "id": "new_task_id",
    "title": "Task Title",
    "projectId": "project_id",
    ...
  },
  "message": "Task 'Task Title' created successfully in project project_id"
}
```

**Use Cases:**
- Create new tasks from natural language requests
- Add tasks with due dates and priorities
- Populate task descriptions

---

### `complete_task`

**Purpose:** Mark a task as completed in TickTick.

**Input:**
- `task_id` (string, required): The ID of the task to complete
- `project_id` (string, required): The ID of the project containing the task

**Output:**
```json
{
  "success": true,
  "message": "Task 'Task Title' marked as completed",
  "task": {
    "id": "task_id",
    "status": 1,
    ...
  }
}
```

**Use Cases:**
- Mark tasks as done when completed
- Update task status programmatically

---

## Resources

Resources provide read-only access to TickTick data.

### `ticktick://projects`

**Purpose:** Get all TickTick projects (lists) as a JSON resource.

**URI Pattern:** `ticktick://projects`

**Returns:** JSON string containing all projects with their IDs, names, and metadata.

**Use Cases:**
- Read project information without using tools
- Access project data as context for LLMs

---

### `ticktick://tasks/{list_id}`

**Purpose:** Get all tasks from a specific project/list as a JSON resource.

**URI Pattern:** `ticktick://tasks/{list_id}` where `{list_id}` is the project ID

**Returns:** JSON string containing all tasks in the specified project.

**Use Cases:**
- Read task data without using tools
- Access task information as context for LLMs
- Browse tasks in a specific project

---

## Discovery

The MCP protocol provides automatic discovery of tools and resources. When an MCP client (like Gemini CLI) connects to this server, it automatically:

1. **Discovers all tools** - Gets names, descriptions, input schemas, and output schemas
2. **Discovers all resources** - Gets URI patterns and descriptions
3. **Validates inputs** - Ensures tool calls match the defined schemas
4. **Provides documentation** - Makes tool descriptions available to LLMs

This is why proper descriptions and schemas are critical - they enable LLMs to understand what each tool does and how to use it correctly.

## Example Usage Flow

1. **List projects** to find available project IDs:
   ```
   list_projects() → Get project_id
   ```

2. **Create a task** in a project:
   ```
   create_task(project_id="...", title="Buy groceries", priority=3)
   ```

3. **List tasks** to see what was created:
   ```
   list_tasks(project_id="...") → Get task_id
   ```

4. **Complete the task** when done:
   ```
   complete_task(task_id="...", project_id="...")
   ```

## Best Practices

- Always use `list_projects` first to discover available project IDs
- Use `list_tasks` to find task IDs before completing or updating tasks
- Include meaningful task titles and descriptions
- Set appropriate priorities (0-5) for task importance
- Use ISO 8601 format for due dates
