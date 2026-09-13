# MusicAdPromo v4

A deliberately simplified 10–15 second music-promo generator.

## Pipeline
Song + lyrics → rank promo hooks → analyze audio mood + lyrical theme → create ONE visual concept → generate ONE hero image → animate that image → attach the selected song segment.

There is no storyboard and no multi-shot continuity system.

## 1. Setup
```bash
cd promo-generator-v4
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
```

Fill `.env` with the same R2 credentials you already use:
```dotenv
R2_ACCOUNT_ID=...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET_NAME=promo-videos
BACKEND_URL=http://localhost:8000
```

## 2. Modal
The existing Modal secret `r2-credentials` must contain the same four R2 values.

Deploy:
```bash
modal deploy modal_app.py
```
The Modal app name is `musicadpromo-v4` and exposes `generate_hero_image` and `animate_promo`.

## 3. Backend
```bash
source .venv/bin/activate
python -m uvicorn backend.main:app --reload
```
Test: http://127.0.0.1:8000/health

## 4. Frontend
In another terminal:
```bash
cd promo-generator-v4
source .venv/bin/activate
python -m streamlit run frontend/app.py
```
Open http://localhost:8501.

## 5. Workflow
1. Upload song.
2. Paste lyrics.
3. Analyze song.
4. Review mood, lyrical theme, selected hook, and visual concept.
5. Generate one hero image. Regenerate/edit until it is good.
6. Edit the motion prompt if desired.
7. Animate the image.
8. The selected 10–15 second source-audio segment is attached automatically.

## Important
v4 intentionally optimizes for animated-cover-art / premium social-promo aesthetics rather than a miniature AI music video. The video worker currently uses CogVideoX-5B-I2V behind one function so the I2V model can be swapped later without redesigning the app.
