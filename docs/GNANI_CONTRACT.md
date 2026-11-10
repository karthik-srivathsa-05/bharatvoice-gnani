# Verified documentation contract (2026-11-10)

Source: https://docs.gnani.ai/api/STT/speech-to-text and its Markdown variant. Documentation describes synchronous REST clips up to 30 seconds.

| Contract | Implemented value |
| --- | --- |
| Method and endpoint | POST `https://api.vachana.ai/stt/v3` |
| Encoding | multipart/form-data |
| Authentication | `X-API-Key-ID` |
| Correlation | `X-API-Request-ID` UUID |
| File field | `audio_file` |
| Model field | `model=prisma-v3.0` |
| Language hint | `language_code=kn-IN,en-IN` |
| Output style | `format=transliterate` |
| Success | `success: true`, string `transcript`, `request_id`, model on nonempty speech |
| Empty speech | May omit model/timings |
| Truncation | `truncated: true`; rejected, ask for shorter audio |
| Upstream audio formats | WAV, MP3, OGG, FLAC, AAC, M4A |
| MVP validated subset | WAV, FLAC, OGG; 0.1–30 seconds, mono/stereo, <=10 MiB |

Upstream HTTP errors include 400 validation/audio errors, 401/403 authentication/scope, 402 credit, 422 validation, 429 rate limiting, 500/503 service errors and 504 timeout. Envelope shapes differ; this MVP branches on HTTP status and returns a sanitized message rather than assuming one error schema.

No live credentials or authorized sample were available. Mocked contract tests verify request construction only. They do not prove upstream acceptance, transcription quality, or account access.
