# Install the four-template build

This ZIP has frontend/, backend/ and shared/ directly at its root.
Copy those folders into the ROOT of the repository your deployed app uses.
Replace files; do not upload them inside a new MusicAdPromo-existing/ folder.
In particular, update shared/templates.py alongside frontend/app.py.

Commit and push the changes to the branch used by Streamlit and the backend.
Reboot Streamlit and redeploy/restart the backend. Click Analyze song again.

The page header should say "Four-template build · Available scenes (4)" and list
River skyline, Neon racecars, Sunset coast, Moonlit dreamscape. If it still shows
only two templates, the deployed branch/files have not updated. This frontend
now stops with a clear error if it loads the older two-template shared module.
The Scene dropdown after analysis includes Automatic plus the four named scenes.
