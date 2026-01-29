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