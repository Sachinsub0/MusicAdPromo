# MusicAdPromo v7 — integration starter

This is a **working standalone prototype of the new selection and alignment workflow**, not a modification of the original project. The latest four-template source ZIP was unavailable. It does **not** render MP4s or preserve the original scene renderer by itself.

## Features
- Duration selector: 10–25 seconds
- Up to five recommended sections using RMS/onset activity heuristic (not an LLM or learned hook ranking)
- Manual start-time selector, preview of chosen clip
- Whisper transcription with word timestamps (optional dependency)
- Multilingual language code option; accuracy varies by language/audio quality
- Editable word timestamps, validation and JSON export
- Explicit fallback for user-supplied lyrics (uniform timing placeholders, **not** forced alignment)

## Run
From project root:
```bash
pip install -r requirements.txt
# For automatic Whisper transcription: pip install faster-whisper
uvicorn backend.main:app --host 0.0.0.0 --port 8000
# in another terminal:
streamlit run frontend/app.py
```
Set `BACKEND_URL` for remote backend. Render start command should run from repo root so `shared` imports work.

## Merge into existing app
1. Copy `shared/audio.py` and `shared/alignment_v7.py` into existing `shared/`.
2. Copy the `/v7/*` routes from `backend/main.py` into your existing FastAPI app (do not replace existing routes).
3. Integrate the selection UI from `frontend/app.py` into your existing Streamlit UI; preserve four original templates and existing render endpoint.
4. Feed selected `start`, `duration`, and corrected word timings into existing rendering code. If render uses absolute timestamps, add `start` to relative clip timestamps exactly once.
5. Add optional forced-alignment model if verified word-level alignment of supplied lyrics is required. Whisper alone does not provide that guarantee.

## Known limitations
- No MP4 render integration without original backend/template source.
- Song ranking is based on onset/loudness, not semantic 'best hooks'.
- Muffled/multilingual singing remains challenging; corrected lyrics are not force-aligned.
- No drag-to-select waveform UI; custom start-time slider provided.
- `faster-whisper` on a 512MB Render instance may exceed memory; use a separate inference service or higher-memory instance.
- File size capped at 30MB; upload handling is in-memory.
