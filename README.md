# Interview Preparation Platform

## OpenAI Speech Integration

### Environment Variables

Set these in your environment or `.env` file:

- `OPENAI_API_KEY`
- `OPENAI_STT_MODEL` (default: `whisper-1`)
- `OPENAI_TTS_MODEL` (default: `gpt-4o-mini-tts`)
- `OPENAI_TTS_VOICE` (default: `alloy`)
- `OPENAI_TTS_OUTPUT_FORMAT` (default: `mp3`)

### Speech-to-Text (HTTP)

```bash
curl -X POST "http://localhost:8080/api/v1/speech/transcribe" \
  -F "audio_file=@/path/to/audio.wav"
```

### Speech-to-Speech (WebSocket)

Connect to `ws://localhost:8080/api/v1/speech/stream` and send:

```json
{"type":"start","session_id":"session_123","search_query_id":1,"tts_enabled":true}
{"type":"audio","chunk":"<base64-audio-bytes>"}
{"type":"end"}
```

The server responds with events like:

```json
{"type":"transcript","data":{"text":"..."}}
{"type":"answer","data":{"token":"..."}}
{"type":"audio_chunk","data":{"chunk":"<base64-audio-bytes>"}} 
{"type":"complete","data":{"response":"...","interview_finished":false}}
```

## Testing

The platform features a comprehensive test suite consisting of unit tests, integration tests, and Playwright end-to-end (E2E) tests.

### Prerequisites

Ensure you have installed the project dependencies, including test requirements:

```bash
poetry install
poetry run playwright install
```

Make sure the local PostgreSQL database and Redis services are running:

```bash
docker compose up -d db redis
```

### Running Unit and Integration Tests

To run the unit and integration test suite (141 tests), execute:

```bash
poetry run pytest tests/unit tests/integration
```

### Running Frontend E2E Playwright Tests

The E2E tests (10 tests) test the React frontend by interacting with a running backend and frontend server. We use a helper script to manage the lifecycle of these servers automatically:

```bash
poetry run -- python /home/work/.gemini/antigravity-cli/skills/webapp-testing/scripts/with_server.py \
  --server "DB_PORT=5435 REDIS_PORT=6380 poetry run python -m src.api.main" --port 8080 \
  --server "npm run dev --prefix ../ui" --port 5173 \
  -- poetry run pytest tests/e2e/test_frontend.py
```

This command will:
1. Start the FastAPI backend API on port `8080`.
2. Start the Vite React development server on port `5173`.
3. Wait until both ports are fully available.
4. Run the 10 Playwright tests.
5. Gracefully terminate both servers once testing completes.