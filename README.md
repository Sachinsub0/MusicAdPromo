# MusicAdPromo v6

**Goal:** combine the atmosphere of the old animated-image ads with lyrics that are actually synchronized to vocals and musical events.

## v6 pipeline
Hook selection → mood/lyric understanding → one hero image → restrained image animation → WhisperX word alignment → beat/onset timeline → kinetic typography → final audio mix.

## Critical timing rule
**WhisperX decides WHEN words appear. Beats/onsets only decide HOW the active typography/background reacts.**
The renderer never redistributes supplied lyrics proportionally across a phrase like v5 did.

WhisperX provides forced word alignment using phoneme ASR models. librosa provides explicit beat and onset event timestamps. v6 combines both into one clip-local master timeline.

## Important v6 MVP choice
Hero-image generation is deliberately decoupled from synchronization. Upload any 9:16 hero image and v6 adds restrained Ken Burns movement plus beat micro-pulses. This lets you validate sync first. The generated `image_prompt` is ready for plugging an image generator back in after timing is proven.

## Requirements
- Python 3.11 or 3.12 recommended
- ffmpeg installed (`brew install ffmpeg` on macOS)
- First WhisperX run downloads its ASR/alignment models and can take a while.

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
1. Upload song + full lyrics.
2. Analyze + align.
3. **Before rendering, inspect the Alignment Check table.** If word start/end times are wrong, don't debug typography yet.
4. Upload a hero image.
5. Render.
6. Verify lyric entry against the vocal and micro-pulses against beats/onsets.

## Next step after sync passes
Reconnect automatic hero-image generation and optional I2V. Keep it as a background layer only; never let generative video own lyric timing.
