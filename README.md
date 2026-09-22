# MusicAdPromo v6.2 — Auto Lyrics

**Goal:** combine the atmosphere of the old animated-image ads with lyrics that are actually synchronized to vocals and musical events.

## v6 pipeline
Hook selection → Demucs vocal separation → WhisperX transcription/alignment → editable lyric review → mood/lyric understanding → one hero image → restrained image animation → beat/onset timeline → kinetic typography → final audio mix.

## Automatic lyrics
- Lyrics are now optional. Leave the correction box blank to transcribe the selected hook directly from the song.
- Demucs first isolates the vocal stem so WhisperX receives less instrumental interference.
- If Demucs is unavailable or fails, the backend safely falls back to transcribing the original mix.
- The detected lyrics appear in an editable review box. After making corrections, click **Re-align corrected lyrics** so the corrected words retain audio-derived timestamps.
- The final video always uses the original song audio, not the isolated vocal stem.

## Critical timing rule
**WhisperX decides WHEN words appear. Beats/onsets only decide HOW the active typography/background reacts.**
The renderer never redistributes supplied lyrics proportionally across a phrase like v5 did.

WhisperX provides forced word alignment using phoneme ASR models. librosa provides explicit beat and onset event timestamps. v6 combines both into one clip-local master timeline.

## Important v6 MVP choice
Hero-image generation is deliberately decoupled from synchronization. Upload any 9:16 hero image and v6 adds restrained Ken Burns movement plus beat micro-pulses. This lets you validate sync first. The generated `image_prompt` is ready for plugging an image generator back in after timing is proven.

## Requirements
- Python 3.11 or 3.12 recommended
- ffmpeg installed (`brew install ffmpeg` on macOS)
- First WhisperX and Demucs runs download their models and can take a while.
- For deployment, run the FastAPI backend on Modal or another host with sufficient memory. Keep Streamlit as the interface and set its `BACKEND_URL` environment variable to the backend URL.

## Setup
```bash
cd promo-generator-v6
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Run
Terminal 1:
```bash
source .venv/bin/activate
python -m uvicorn backend.main:app --reload
```

Terminal 2:
```bash
source .venv/bin/activate
python -m streamlit run frontend/app.py
```

Open http://localhost:8501.

## Test sequence
1. Upload a song. Lyrics are optional.
2. Click **Analyze + align**.
3. Review the detected lyrics. Correct any mistakes and click **Re-align corrected lyrics**.
4. **Before rendering, inspect the Alignment Check table.** If word start/end times are wrong, don't debug typography yet.
5. Upload a hero image.
6. Render and verify lyric entry against the vocal and micro-pulses against beats/onsets.

## Optional environment settings
```bash
ENABLE_VOCAL_SEPARATION=1  # set to 0 to skip Demucs
DEMUCS_MODEL=htdemucs
WHISPER_MODEL=small
WHISPER_LANGUAGE=en
WHISPER_BATCH_SIZE=4
```

## Next step after sync passes
Reconnect automatic hero-image generation and optional I2V. Keep it as a background layer only; never let generative video own lyric timing.


## v6.1 responsive lyric layout
The renderer now guarantees lyric visibility inside the 9:16 safe area:
- automatic line wrapping,
- adaptive font sizing,
- up to four centered lines per phrase,
- fixed word slots so active-word scaling does not reflow neighboring words,
- defensive horizontal clamping,
- upcoming/current/past words remain readable.
