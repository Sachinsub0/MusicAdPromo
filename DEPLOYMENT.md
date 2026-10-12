# Deploy both parts together

Copy backend/, frontend/, shared/, tests/, requirements.txt, README.md, and .gitignore into your existing Git clone. Preserve existing .env, secrets, and deployment configuration. Commit and push.

## Backend (Render)
Deploy the latest commit of the repository containing these files. Run from the repository root with:

    python -m uvicorn backend.main:app --host 0.0.0.0 --port $PORT

Install the root requirements.txt and ffmpeg. Use Python 3.11. The model pipeline requires sufficient memory. Verify /health returns version MusicAdPromo-v6.3.1-templates.

## Frontend (Streamlit Cloud)
Use frontend/app.py as entrypoint. frontend/requirements.txt keeps the frontend installation small. Set BACKEND_URL to your deployed backend URL using a top-level Streamlit secret, for example:

    BACKEND_URL = "https://musicadpromo.onrender.com"

Use your actual backend URL. Refresh the interface and analyze the song again after both deployments finish. Old plans are rejected with a clear version mismatch message rather than rendering a blank background.

## Context-aware lyric mood
Deploy frontend/app.py and all shared files together. Reboot Streamlit, restart
the backend, then analyze again. To enable AI meaning/context analysis, add to
Streamlit secrets:
```toml
OPENAI_API_KEY = "your-api-key"
LYRIC_MOOD_MODEL = "gpt-4o-mini"
```
Set the same environment variables on the backend. Keep keys out of GitHub.
AI analysis sends hook lyrics (up to 16,000 characters), not audio, to OpenAI;
API usage charges apply. Set LYRIC_MOOD_AI="false" for offline-only analysis.
The UI identifies the active method and reports fallback when the key is absent,
the service fails, or AI is uncertain. Successful results are cached in memory;
edited lyrics receive new analysis. Review transcription before choosing a mood.
The existing three scenes remain: melancholic/dark → River skyline;
romantic/dreamy → Moonlit dreamscape; confident/celebratory → Neon racecars.
Distinct moods can share a scene. AI is probabilistic; manual selection remains.
