# Gemini CLI Agent Notes for ticktick-access repository

This document provides guidelines and context for the Gemini CLI agent when working within the `ticktick-access` repository.

## Content Placement Guidelines

To maintain clarity and separation of concerns in documentation, please adhere to the following guidelines:

*   **`VENDOR-API.md`**: This file is strictly for documenting raw API interaction with the TickTick platform using generic `curl` commands. It should detail authentication flows, API endpoints, request/response formats, and any vendor-specific limitations. **It should NOT contain information about our internal MCP server product, Docker testing steps, or any other contributor-specific development process.**

*   **`README.md`**: This file serves as the primary user-facing documentation for setting up and running the `ticktick-access` MCP server. It should include quick start guides, Docker setup instructions for users, and configuration information. It focuses on **usage and configuration, not on maintenance or extension of the MCP server.**

*   **`CONTRIBUTING.md`**: This file is for contributors and developers. It includes guides on setting up a development environment, **how to build, run, and test changes to tools (including Docker-based testing steps)**, and other development-specific information.

*   **`GEMINI.md` (this file)**: This file is specifically for internal notes and instructions for the Gemini CLI agent. It captures meta-information about the repository's structure, conventions, and specific instructions for the agent's workflow.

## Sensitive Information Handling

*   **`TICKTICK_ACCESS_TOKEN`**: This token is sensitive and should **never** be hardcoded into any script, documentation, or committed to version control. It must always be loaded from a secure source, such as the `.env` file (which is `.gitignore`d) or environment variables. All examples and tool implementations should respect this. When testing, ensure that the token is passed securely (e.g., via Docker environment variables or loaded from a mounted `.env`).
