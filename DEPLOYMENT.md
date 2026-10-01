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
