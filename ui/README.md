# Interview Preparation Platform UI

## Run Locally

1. Install dependencies (make sure `streamlit`, `httpx`, and `websockets` are installed).
2. Start the UI:
   ```bash
   streamlit run ui/main.py
   ```

## Configuration

Environment variables are read from `.env` at the repo root:

- `ML_API_BASE_URL` (default: `http://localhost:32453/api/v1`)
- `PAGE_TITLE` (optional)
- `PAGE_ICON` (optional)
- `LAYOUT` (optional)

## Voice Messages

The chat page supports voice input/output using the `/speech/stream` WebSocket.
Record a message, send it, and the assistant response will be played back if TTS is enabled.
