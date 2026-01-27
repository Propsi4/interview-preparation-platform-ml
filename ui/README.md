# Interview Preparation Platform UI

## Run Locally

1. Install dependencies (make sure `streamlit` and `httpx` are installed).
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
