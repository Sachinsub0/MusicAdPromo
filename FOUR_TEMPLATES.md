# Four mood-based templates

- Neon racecars: confident, aggressive and dark moods.
- Moonlit dreamscape: melancholic, sad and dreamy moods.
- Sunset coast: romantic, celebratory and hopeful moods.
- River skyline: neutral or unclear mood fallback; also manually selectable.

Primary mood takes priority; legacy mood lists use a compatible fallback mapping.
All four scenes are animated presets. Mood analysis remains separate from drawing
scenes: optional AI reads the hook lyrics, offline rules remain the fallback.
Manual scene selection and the final MP4 download remain available.
No scene comparison panel, comparison tracking, or results CSV export remains.

Deploy frontend/app.py, backend/main.py and the entire shared folder. Reboot both
services and Analyze song again. Keep OPENAI_API_KEY in Streamlit secrets and the
backend environment to enable AI lyric meaning analysis. API charges apply and
hook lyrics are sent to OpenAI. No accuracy or 90% coverage claim has been measured.
