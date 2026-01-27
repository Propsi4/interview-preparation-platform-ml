# PET UI

## Description

The **PET UI** is the user-facing component of the Project Estimation Tool. It provides an intuitive interface for users to interact with the AI agents, creating new project estimations and reviewing past results.

## Tech Stack

-   **Framework:** Streamlit

## Features & Pages

The application is structured into several key pages, each serving a specific workflow:

### Chat (`/pages/chat.py`)
The core interactive interface where users collaborate with the AI.
-   **Streaming Responses:** Provides real-time feedback by displaying the AI's "Reasoning" process separately from the final "Answer".
-   **Status Updates:** Visual indicators show the current state of the orchestrator (e.g., "Thinking...", "Complete").
-   **Specialist Profile Insertion:** A helper tool in the sidebar allows users to fetch available specialist profiles from the backend and insert them directly into the chat prompt for context.
-   **Attachment Handling:** Automatically renders download buttons for generated files (e.g., DOCX proposals) returned by the agents.
-   **Session Management:** Maintains chat history across reloads.

### History (`/pages/history.py`)
Allows users to browse and load previous estimation sessions.
-   **Session List:** Displays a chronological list of past interactions.
-   **Session Loading:** Restores the full context and message history of a selected session.

### Home (`/pages/home.py`)
The landing page providing a project overview and quick navigation links.

## Architecture

The UI decouples presentation logic from API communication using a dedicated client layer:

-   **PETClient (`ui/api/client.py`):** Handles all asynchronous HTTP communication with the **ML Service** and **Backend**. It abstracts away the complexity of:
    -   Streaming chat events (Server-Sent Events).
    -   Fetching specialist profiles.
    -   Retrieving chat history.

## Configuration

The application is configured via environment variables (see `ui/config/settings.py`):

-   **API Endpoints:**
    -   `ML_API_BASE_URL`: URL of the AI/ML service.
    -   `BACKEND_BASE_URL`: URL of the Django backend.
-   **Authentication:**
    -   `DJANGO_SUPERUSER_USERNAME` & `DJANGO_SUPERUSER_PASSWORD`: Credentials for backend token authentication.
-   **Page Config:**
    -   `PAGE_TITLE`: Custom title for the browser tab.
    -   `PAGE_ICON`: Favicon emoji.
    -   `LAYOUT`: Streamlit layout mode (e.g., "wide").
