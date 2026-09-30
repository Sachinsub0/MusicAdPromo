# MusicAdPromo v6.3 — Templates + editable lyric alignment

Upload a song, analyze a 10–15 second hook, review its lyrics, and render a vertical animated lyric video. No background upload or external image service is required.

## What changed
- Three bundled, code-drawn animated templates: **River skyline**, **Neon racecars**, and **Moonlit dreamscape**. These are stylized illustrations, not photographic footage.
- Automatic template selection uses the existing lyric mood/keyword analysis and acoustic energy. You can override the selection before rendering. Mood classification is a lightweight heuristic, not a trained emotion classifier.
- Accent-colored active words, outlined highlight tiles, beat pulses, and semantic motion. Upcoming and previous words remain visible within the current phrase, with responsive wrapping.
- Editing Detected lyrics immediately updates every word in Alignment check, including insertions and deletions. Changed spans show provisional estimated timing.
- **Re-align corrected lyrics** passes the exact hook text to WhisperX forced alignment. Rendering is disabled while unsaved lyric edits are pending. The backend also rejects a mismatch between lyrics and alignment words.
- Untimed words are retained and labeled Estimated. Their times are interpolated between measured anchors; review these before exporting. Forced alignment does not guarantee accuracy for sung vocals or incorrect lyrics.

## Run locally
Use Python 3.11 and install ffmpeg (`brew install ffmpeg` on macOS).

```bash
cd MusicAdPromo
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m uvicorn backend.main:app --reload
```

In another terminal:

```bash
cd MusicAdPromo
source .venv/bin/activate
python -m streamlit run frontend/app.py
```

Open http://localhost:8501. First analysis downloads WhisperX and Demucs models. The backend needs enough memory for both. The frontend uses `BACKEND_URL`, defaulting to http://127.0.0.1:8000; set it to your deployed backend URL for Streamlit Cloud.

## Use
1. Upload your song and click **Analyze song**. Optional supplied lyrics must describe only the selected hook, not the full song.
2. Review Detected lyrics. Edit misheard words, then click **Re-align corrected lyrics**.
3. Inspect Alignment check, particularly any Estimated times. Vocal timing controls word highlighting; beats control animation only.
4. Choose Automatic or a specific visual template, then render.

Changing the uploaded song clears the old plan/video. Changing promo length requires another analysis. Hook candidates can be selected before correcting lyrics.

## Environment
```bash
ENABLE_VOCAL_SEPARATION=1
DEMUCS_MODEL=htdemucs
WHISPER_MODEL=small
WHISPER_LANGUAGE=en
WHISPER_BATCH_SIZE=4
BACKEND_URL=http://127.0.0.1:8000
```
If vocal separation fails, the original mix is used. Output audio always comes from the original song.

## Verification
```bash
python -m unittest discover -s tests -v
```
Tests cover lyric additions/deletions/repeated words, punctuation and missing timestamps, corrected text passed to forced alignment, and scene selection/animation. A short synthetic-audio render was also checked. Real-song transcription and deployment require testing on your backend; they were not run with a real song in this update.
