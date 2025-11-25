# TickTick v1 API Guide for `curl` Users

This document provides a guide to authenticating with the TickTick API and using `curl` to perform common operations. It is intended for direct command-line interaction with the raw TickTick API.

## 1. One-Time Setup on TickTick Developer Portal

Before using the API, you must register an application with TickTick.

1.  Navigate to [developer.ticktick.com](https://developer.ticktick.com/) and sign in.
2.  Click on **Manage Apps** in the top navigation bar.
3.  Click **"Create an app"** or edit an existing application.
4.  On your application's page, you will find the **"Client ID"** and **"Client SECRET"**. You will need these for your local environment setup.
5.  Set the **"OAuth redirect URL"** to the following exact value:
    ```
    http://localhost:8080
    ```
    This is crucial for the authorization flow to redirect correctly.

## 2. Obtaining Your Access Token (Manual OAuth 2.0 Flow)

The TickTick API uses OAuth 2.0. You will need to manually obtain an access token to make authenticated API calls. This involves initiating an authorization request, getting an authorization code, and then exchanging that code for an access token.

**Step A: Get an Authorization Code**

1.  **Construct the Authorization URL:**
    Replace `YOUR_CLIENT_ID` with your actual Client ID and `YOUR_SCOPE` with the desired scopes (e.g., `tasks:read tasks:write`). The `redirect_uri` must exactly match what you registered.
    ```
    https://ticktick.com/oauth/authorize?client_id=YOUR_CLIENT_ID&scope=YOUR_SCOPE&redirect_uri=http://localhost:8080&state=random-string-for-security&response_type=code
    ```
2.  **Open in Browser:** Open this constructed URL in your web browser.
3.  **Authorize:** Log in to TickTick and grant permission to your application.
4.  **Capture Code:** Your browser will be redirected to `http://localhost:8080/?code=YOUR_AUTHORIZATION_CODE&state=random-string-for-security`. Copy the `YOUR_AUTHORIZATION_CODE` value.

**Step B: Exchange Authorization Code for an Access Token**

Use `curl` to exchange the authorization code for an access token. Replace `YOUR_CLIENT_ID`, `YOUR_CLIENT_SECRET`, and `YOUR_AUTHORIZATION_CODE` with your actual values.

```bash
curl -X POST "https://ticktick.com/oauth/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "client_id=YOUR_CLIENT_ID" \
     -d "client_secret=YOUR_CLIENT_SECRET" \
     -d "code=YOUR_AUTHORIZATION_CODE" \
     -d "grant_type=authorization_code" \
     -d "redirect_uri=http://localhost:8080" \
     -d "scope=tasks:read tasks:write" | jq
```
The response will be a JSON object containing your `access_token` and other token information. Extract the `access_token` value.

**Token Expiration:** TickTick API access tokens typically expire after a certain period (e.g., 24 hours). When a token expires, API calls will start to fail with authentication errors (e.g., HTTP 401 Unauthorized). You will need to repeat this process to obtain a new token.

## 3. Manual API Calls with `curl`

Once you have a valid `access_token`, you can use it to make direct API calls with `curl`.

### Loading Environment Variables

It's convenient to load your `access_token` into a shell environment variable. Replace `YOUR_ACCESS_TOKEN` with the token you obtained.

```bash
export TICKTICK_ACCESS_TOKEN="YOUR_ACCESS_TOKEN"
```

### Example API Calls

*Note: The `... | jq` at the end of the commands is optional, but recommended. It pipes the JSON output to the `jq` tool for pretty-printing, making it much easier to read.*

#### List all Projects

This command fetches all of your projects (which TickTick also refers to as "lists").

```bash
curl -X GET "https://api.ticktick.com/open/v1/project" \
     -H "Authorization: Bearer $TICKTICK_ACCESS_TOKEN" | jq
```

#### Work Project ID

For the following examples, we will assume a "Work" project exists. You can replace `YOUR_PROJECT_ID` with any other project ID you obtain from the "List all Projects" call.

#### List Tasks in a Specific Project

This command fetches all the data, including tasks, for a given project ID.

```bash
curl -X GET "https://api.ticktick.com/open/v1/project/YOUR_PROJECT_ID/data" \
     -H "Authorization: Bearer $TICKTICK_ACCESS_TOKEN" | jq
```

#### Add a New Task to a Project

This command adds a new task to a specified project. The response will contain the `id` of the newly created task.

```bash
curl -X POST "https://api.ticktick.com/open/v1/task" \
     -H "Authorization: Bearer $TICKTICK_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{ \
         "projectId": "YOUR_PROJECT_ID", \
         "title": "This is a dummy task from API" \
     }' | jq
```
*(Remember to capture the `id` from the response of this command for the next steps.)*

#### Update an Existing Task

To update an existing task (e.g., to mark it as complete, or modify its title/content), use a `POST` request to the `/open/v1/task/{taskId}` endpoint.

**IMPORTANT**: When updating a task, it is crucial to include *all* fields from the task's original `GET` request in the `POST` request payload. If fields are omitted, they may be inadvertently set to `null` or default values by the API.

Here's a detailed example of how to update a task, demonstrating how to retrieve existing fields and then modify specific ones:

1.  **Load your `TICKTICK_ACCESS_TOKEN` from `.env`**:
    ```bash
    export $(cat .env | xargs)
    ```

2.  **Retrieve the full details of the task you want to update**:
    You'll need the `PROJECT_ID` of the task's parent project and the `TASK_ID` of the task itself.

    ```bash
    # Replace YOUR_PROJECT_ID and YOUR_TASK_ID with actual values
    PROJECT_ID="YOUR_PROJECT_ID"
    TASK_ID="YOUR_TASK_ID"

    # Fetch all tasks from the project and filter for the specific task
    TASK_DETAILS=$(curl -X GET "https://api.ticktick.com/open/v1/project/$PROJECT_ID/data" \
         -H "Authorization: Bearer $TICKTICK_ACCESS_TOKEN" | \
    jq ".tasks[] | select(.id == \"$TASK_ID\")")

    echo $TASK_DETAILS | jq
    ```
    This will output the full JSON object of the task. Copy this entire JSON object.

3.  **Modify the desired fields and update the task**:
    Take the full JSON object you copied in the previous step. Modify the `title`, `content`, `priority`, `dueDate`, `status`, or any other field you wish to change. Then, use this modified JSON in the `-d` payload of your `curl` command.

    For example, to update the title and content of a task:

    ```bash
    export $(cat .env | xargs) # Ensure token is loaded
    TASK_ID="GENERIC_TASK_ID" # Example Task ID
    
    curl -X POST "https://api.ticktick.com/open/v1/task/$TASK_ID" \
         -H "Content-Type: application/json" \
         -H "Authorization: Bearer $TICKTICK_ACCESS_TOKEN" \
         -d '{
             "id": "GENERIC_TASK_ID",
             "projectId": "GENERIC_PROJECT_ID",
             "sortOrder": 12345,
             "title": "Example: Follow-up with Product on Generic Feedback",
             "content": "Example: Discuss feedback from the engineering team regarding product X on DATE with NAME.",
             "startDate": "GENERIC_DATE",
             "dueDate": "GENERIC_DATE",
             "timeZone": "America/Los_Angeles",
             "isAllDay": true,
             "priority": 3,
             "repeatFlag": "",
             "status": 0,
             "etag": "GENERIC_ETAG",
             "kind": "TEXT"
         }' | jq
    ```
    *(Note: The `etag` field is often returned by the API but is not strictly required in the update payload. However, including it from the original task details can be good practice.)*


## Limitations (Vendor API)

*   **Inbox List:** It is generally not possible to directly access the "Inbox" as a named list or project via the v1 API. Tasks intended for the Inbox typically need to be assigned to a specific project.
*   *(Add other raw API limitations as they are discovered or become relevant.)*

port $(cat .env | xargs)
```

### Example API Calls

*Note: The `... | jq` at the end of the commands is optional, but recommended. It pipes the JSON output to the `jq` tool for pretty-printing, making it much easier to read.*

#### List all Projects

This command fetches all of your projects (which TickTick also refers to as "lists").

```bash
curl -X GET "https://api.ticktick.com/open/v1/project" \
     -H "Authorization: Bearer $TICKTICK_ACCESS_TOKEN" | jq
```

#### Work Project ID

For the following examples, we will use the "Work" project, which has the ID `YOUR_PROJECT_ID`. You can replace this with any other project ID you obtain from the "List all Projects" call.

#### List Tasks in the "Work" Project

This command fetches all the data, including tasks, for the "Work" project.

```bash
curl -X GET "https://api.ticktick.com/open/v1/project/YOUR_PROJECT_ID/data" \
     -H "Authorization: Bearer $TICKTICK_ACCESS_TOKEN" | jq
```

#### Add a Dummy Task to the "Work" Project

This command adds a new task to the "Work" project. The response will contain the `id` of the newly created task, which you will need for updating or deleting it.

```bash
curl -X POST "https://api.ticktick.com/open/v1/task" \
     -H "Authorization: Bearer $TICKTICK_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
         "projectId": "YOUR_PROJECT_ID",
         "title": "This is a dummy task from API"
     }' | jq
```
*(Remember to capture the `id` from the response of this command for the next steps.)*

#### Update an Existing Task

To update an existing task (e.g., to mark it as complete, or modify its title/content), use a `POST` request to the `/open/v1/task/{taskId}` endpoint.

**IMPORTANT**: When updating a task, it is crucial to include *all* fields from the task's original `GET` request in the `POST` request payload. If fields are omitted, they may be inadvertently set to `null` or default values by the API.

```bash
curl -X POST "https://api.ticktick.com/open/v1/task/{{taskId}}" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $TICKTICK_ACCESS_TOKEN" \
     -d '{
         "id": "{{taskId}}",
         "projectId": "{{projectId}}",
         "title": "Updated Task Title",
         "status": 1,
         "priority": 1
         // ... include all other fields from the original GET request
     }' | jq
```