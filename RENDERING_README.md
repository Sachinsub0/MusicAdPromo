# MusicAdPromo v7 — Rendering addition

This package adds four **new procedural interpretations** of the Neon Racecars, Skyline, Nightclub, and Sunset Coast scenes. It does **not** restore the exact original animations or assets because the original working repository was unavailable.

## Added
- `shared/render_v7.py`: FFmpeg + Pillow-based 9:16 MP4 renderer, audio included, optional lyric overlays
- `POST /v7/render`: accepts multipart `audio`, `start`, `duration`, `template`, `words_json` and returns an MP4
- `GET /v7/templates`
- Streamlit scene selection, render preview, and MP4 download button

## Deploy
- Merge this package with your repository, preserving any existing template renderer and other API routes.
- Add Pillow to Render requirements, and ensure `ffmpeg` executable is installed on Render (`which ffmpeg`).
- Render runs `uvicorn backend.main:app --host 0.0.0.0 --port $PORT` if this is your app entrypoint.
- Redeploy Streamlit frontend and Render backend from the same commit.
- The `/v7/render` request is synchronous and holds the response in memory; longer videos and concurrent users can exceed free hosting limits. Use object storage/job queue for production.

## Verification
A 10-second generated silent-audio clip was rendered with the Sunset Coast scene; resulting bytes had an MP4 `ftyp` header. This is not an end-to-end test against your hosted app.

## Important
Existing four legacy template source files and original MP4 renderer were not accessible in this session. To preserve the **exact** original look, provide the last working repository ZIP and integrate its `shared/templates.py` and rendering pipeline instead of these fallback scenes.
