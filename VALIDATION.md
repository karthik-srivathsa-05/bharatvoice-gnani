# Validation report — November 10, 2026

## Result

- Python **3.12.14**; **52 pytest tests passed, 0 failed**.
- One upstream Starlette/httpx TestClient deprecation warning. It did not fail the suite.
- Five hand-authored **synthetic** scenarios: engine **5/5**, baseline **0/5**, ordered category/location/time exact match. Fixtures were known during implementation; no held-out or live STT claim.
- Headless Chromium smoke passed against a running Uvicorn process: two issues, missing-location gate, one-issue clarification, explicit confirmation, page-reload persistence, manual arbitrary-address edit and confirmation revocation, 390px mobile layout, no JavaScript page errors.
- A separate browser check used Chromium's **synthetic microphone device**, recorded a WAV, validated it with the server's audio validator and displayed playback. It did not send audio upstream.
- Actual HTTP `/api/health` returned `ok: true`, `gnani_configured: false`, model `prisma-v3.0`, and `live_verified: false`.
- Actual HTTP root, JS asset and diagnostics endpoints were checked; API tests also exercise session creation/resume, corrections, field review, confirmations, conflicts, missing sessions and audio rejection.
- No deployment, publication, government submission or live Gnani request was performed.

## Commands run

```bash
python -m venv .venv
.venv/bin/pip install fastapi 'uvicorn[standard]' pydantic pytest httpx python-multipart python-dotenv soundfile playwright
curl -L --max-time 30 https://docs.gnani.ai/api/STT/speech-to-text
curl -L --max-time 30 https://docs.gnani.ai/api/STT/speech-to-text.md
.venv/bin/python -m pytest -q
.venv/bin/python evaluate.py
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
PLAYWRIGHT_BROWSERS_PATH=work/browsers .venv/bin/python -m playwright install chromium
PLAYWRIGHT_BROWSERS_PATH=work/browsers .venv/bin/python tests/browser_smoke.py
curl http://127.0.0.1:8000/api/health
```

The first test collection failed because the standalone pytest launcher did not place the project directory on its import path. `pyproject.toml` now supplies `pythonpath = ["."]`; documented test commands use `python -m pytest`. A later regression test was corrected to distinguish an incomplete location (already correctly blocked by a missing-field gate) from an unrecognized correction requiring a clarification block. Final suite: **52 passed**. The first browser install attempted a nonwritable home cache; setting the workspace-local `PLAYWRIGHT_BROWSERS_PATH` fixed it.

## Main installed versions used

| Package | Version |
| --- | --- |
| FastAPI | 0.162.2 |
| Pydantic | 2.14.3 |
| Uvicorn | 0.54.0 |
| Starlette | 1.10.0 |
| httpx | 0.28.1 |
| pytest | 9.2.0 |
| python-multipart | 0.0.33 |
| python-dotenv | 1.2.4 |
| SoundFile | 0.14.0 |
| Playwright (optional browser check) | 1.65.0 |

## Integration status and limitations

The REST contract was read from Gnani's official documentation, and the application has a real network adapter with explicit Prisma v3.0 selection. No secret bindings were configured. Request construction and error handling were verified with synthetic mocked HTTP responses, **not** a live service. The actual key/account/model/recognized text remain unverified until the user configures a key and sends authorized audio.

The offline extractor uses a small vocabulary and grammar; test success does not demonstrate multilingual robustness, accent fairness, calibrated confidence or production readiness. Manual field review is available for arbitrary addresses and service clarification. Location dispatch precision and semantic action completeness are not validated. The app is a local prototype without authentication. All verification data was synthetic.

See `README.md` for exact startup, architecture, supported grammar, data persistence and remaining live verification steps; `DEMO_STORYBOARD.md` for the 60-second demo. Machine-readable results: `evidence/evaluation.json`; test output: `evidence/pytest.txt`.

## Repository handoff recheck

The existing implementation, README, source, fixtures and tests were inspected in place; no project was recreated. Pytest was rerun and returned **52 passed, 0 failed**, with the same upstream deprecation warning. A fresh Uvicorn process on localhost port 8011 started successfully; the root returned HTTP 200 and health reported `ok: true`, `gnani_configured: false`, and `live_verified: false`. The verification process was stopped afterward. Official Gnani REST documentation was fetched again and confirmed the adapter's endpoint, authentication header, multipart file field, explicit `prisma-v3.0`, language hints and transliteration format.

`GNANI_API_KEY` was checked without printing its value and was unavailable after loading the project `.env` configuration. No live transcription was attempted, so there is no live HTTP status or transcription result to report. All existing fixture and mocked HTTP results remain synthetic.

The intended GitHub repository is `karthik-srivathsa-05/bharatvoice-gnani`, with default branch `main`. Authenticated metadata and `git ls-remote` showed an empty repository before initialization. The existing files were prepared for an initial main-branch commit, with environment files (except the empty `.env.example` template), audio recordings, local databases, caches, virtual environment and scratch data excluded. The final commit and push status are reported separately after verification. No demo deployment or hosting publication is part of this handoff.
