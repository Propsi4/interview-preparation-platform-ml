# Interview Preparation Platform

## ElevenLabs Speech Integration

### Environment Variables

Set these in your environment or `.env` file:

- `ELEVENLABS_API_KEY`
- `ELEVENLABS_TTS_VOICE_ID`
- `ELEVENLABS_TTS_MODEL_ID` (default: `eleven_multilingual_v2`)
- `ELEVENLABS_TTS_OUTPUT_FORMAT` (default: `mp3_44100_128`)
- `ELEVENLABS_TTS_OPTIMIZE_STREAMING_LATENCY` (default: `2`)
- `ELEVENLABS_STT_MODEL_ID` (default: `scribe_v1`)
- `ELEVENLABS_STT_LANGUAGE_CODE` (optional)
- `ELEVENLABS_STT_ENABLE_LOGGING` (default: `true`)

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