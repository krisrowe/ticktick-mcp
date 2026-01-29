# Task Sovereignty and Synchronization Vision

## Overview
This document outlines the transition of task data from being "rented" from a third-party SaaS to being "owned" locally. Task data is often the most valuable personal data, serving as a diary, log, or procedural manual. Unlike email or documents, users often lack sovereignty over their task lists. This strategy ensures long-term preservation, high performance, and resilience.

## Core Goals
### 1. Data Sovereignty & Ownership
- **Permanence**: Tasks are never lost. We are not at the whims of a SaaS company's longevity or business decisions.
- **Indexing & Search**: Full control over indexing the data for instant search and historical analysis.
- **Journaling**: Recognizing tasks as a diary/log of activities, procedures, and historical records.

### 2. Privacy & Compliance
- **Employer/Client Confidentiality**: Minimize exposure of sensitive client or employer data on third-party SaaS platforms (often "fly-by-night" or lacking enterprise-grade security controls).
- **Reduced Third-Party Footprint**: By owning the data locally and treating the vendor only as a transient UX layer, we reduce the risk associated with storing confidential procedural logs or project details indefinitely on external servers.

### 3. Resilience and Stability
- **Connection/Auth Tolerance**: Operations should not fail immediately if an OAuth token expires or the third-party API is temporarily down.
- **Vendor Abstraction**: Protect against breaking API changes, throttling, or Terms of Service shifts by the provider.
- **Data Safety**: Avoid data loss during vendor migrations or sync errors.

### 4. High Performance & AI Readiness
- **Instant Search**: Local regex and semantic search across all folders/projects.
- **AI Integrations**: Providing a fast, structured, and local data source for LLMs and agents to process without API bottlenecks.

## Architectural Vision: Multi-Layer Sync
The architecture potentially supports two layers of synchronization:
1.  **Primary Layer**: A central/local database (e.g., SQLite/PostgreSQL) that serves as the "source of truth."
2.  **UX/Vendor Layer**: One or more third-party platforms (like TickTick) serve as a specialized "UX layer" or "client" for the data, rather than the primary owner.

## Implementation Roadmap
- **SDK Sync**: `sync_all()` to populate a local XDG cache.
- **Write-Through Cache**: All SDK operations update the local state immediately.
- **Centralized Coordination**: Optional GCP Cloud Run service to manage state changes and multi-platform sync.

## Status
**PENDING**. This is a design reference and vision statement.