# Temporary mood and scene comparison build

Editable: lyric mood labels and explanations, scene routing, palette, animation,
font styling and beat-driven effects. Scenes are drawn presets, not AI video.
Lyric meaning is analyzed through OpenAI when configured; audio processing finds
hooks, tempo, beats and vocal alignment separately. The mood model receives lyrics,
not the audio waveform. Correct transcription before comparing results.

Neon racecars is removed from available templates. All recognized moods, including
aggressive car lyrics and sad lyrics, temporarily route to Moonlit dreamscape.
River skyline remains the unknown-mood fallback and manual comparison alternative.
The mood classifier still distinguishes dark/confident from melancholic; using the
same scene is a controlled baseline, not evidence that the classifier is correct.

Deploy frontend/app.py, backend/main.py and the entire shared folder together.
Set OPENAI_API_KEY in Streamlit secrets AND backend environment; optionally set
LYRIC_MOOD_MODEL (default gpt-4o-mini). Reboot both and Analyze song again.
API charges apply, and hook lyrics are sent to OpenAI. The app retries transient
network/server errors once, validates output, and reports offline fallback.
Configured frontend AI now replaces legacy backend analysis instead of silently
accepting old mood labels. No key means offline analysis, not AI success.

Open "Compare scenes and check mood results". Compare A (Moonlit) and B (River),
enter your expected mood, pick a scene, save, then download the CSV before leaving.
Results are session-local, deduplicated per audio/hook/lyric version. Preview images
compare the backgrounds; manually render each scene to compare full moving videos.
This is a side-by-side check, not a blinded/randomized A/B experiment.

90% target = accepted semantic AI results / saved reviewed excerpts. Mood agreement
is reported separately. Use at least 20 distinct real-song excerpts (10 obvious
aggressive/car and 10 obvious sad), with expected labels selected before viewing
predictions if possible. 18/20 is 90% coverage, not proof of 90% classification
accuracy. Use a fresh session for the comparison and avoid changing lyrics between
A and B. No real-song or live API coverage has yet been measured for this build.
