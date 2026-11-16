# MusicAdPromo v7: 200 MB uploads and held-word karaoke

## Changes
- FastAPI `/v7/hooks`, `/v7/preview`, `/v7/align`, `/v7/render` now accept audio up to **200 MiB (209,715,200 bytes)** instead of 30 MiB. Uploaded file length is checked before reading its bytes.
- Streamlit rejects files above the same limit with an understandable error.
- Editing the lyric text box now retains Whisper word timestamps for unchanged words and one-for-one corrected words. A word originally held for 2.5 seconds remains held for 2.5 seconds. Inserted or removed words still require manual timing review.
- The karaoke highlight persists for each word's `start`–`end` interval, with a progress underline during sustained syllables.

## Deploy
Deploy **both** `backend/main.py` and `frontend/app.py`, plus `shared/alignment_v7.py` and `shared/render_v7.py`, from the same commit. Retain existing renderer/assets if you have the actual legacy template files; this package contains the v7 procedural recreations, not the original v6 artwork.

Streamlit Community Cloud normally has a 200 MB upload limit; if overridden, set `.streamlit/config.toml` to `maxUploadSize = 200`. The Streamlit app still sends the full file for each request. On Render, request-size limits, RAM, timeouts, and FFmpeg availability can still prevent 200 MB files from processing. A successful 200 MB HTTP upload is **not** a guarantee that a 200 MB file can be decoded or rendered on a small Render instance. For production use, upload once to object storage and pass a reference, rather than repeatedly uploading the same file to each endpoint.

## Accuracy caveat
Whisper word timestamps are estimates, not forced alignment to corrected lyrics. The editor now preserves timing for unchanged/corrected words instead of evenly redistributing every word, and visual highlighting follows each actual interval. For muffled or multilingual vocals, inspect the word timing editor; this patch does not add a new multilingual forced-alignment model.

## Checks run
Python compilation; 5 pytest tests (including stretched-word preservation); a local 10-second Skyline MP4 rendering smoke test with a 3-second held word. Live Streamlit/Render deployment not tested.
