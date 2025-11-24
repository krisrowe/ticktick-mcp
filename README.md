# TickTick Access

This project provides tools and examples for personal agentic access to the TickTick task platform's API. It serves as a foundation for building custom integrations and automations with TickTick.

This project may evolve into a full-fledged MCP (Multi-platform Command and Control Plane) server for TickTick, providing a unified interface for managing tasks and other data.

## Configuration

This repository requires personal API credentials for accessing the TickTick API. These credentials are not committed to the repository and must be managed locally.

### Manual `.env` Configuration

To use this project, you must provide your own TickTick API credentials in a `.env` file at the root of the repository.

1.  Create a file named `.env`.
2.  Add your credentials to the file. Based on my analysis, the variables should be structured like this:

    ```bash
    # .env
    TICKTICK_USERNAME="your_email@example.com"
    TICKTICK_PASSWORD="your_password"
    TICKTICK_CLIENT_ID="your_client_id"
    TICKTICK_CLIENT_SECRET="your_client_secret"
    ```
    
    *(Please let me know if these variable names are incorrect.)*

### Synchronizing Configuration (`.ws-sync` and `devws`)

The `.env` file is listed in `.gitignore` and will not be committed. To manage this and other important local files across different workstations, this project includes a `.ws-sync` file.

The `.ws-sync` file is simply an inventory of files that are not part of the git repository but are essential for the project to run. These are files that you need to manually maintain and synchronize between your development environments.

For automated backup and restoration of these files, we recommend using the `devws` (Development Workstation Setup) CLI tool.

*   **`devws` Repository**: [https://github.com/krisrowe/chromeos-dev-setup](https://github.com/krisrowe/chromeos-dev-setup)

Please note that the `devws` CLI is not yet publicly available. Until it is, you should manually manage your `.env` file and any other files listed in `.ws-sync`.
