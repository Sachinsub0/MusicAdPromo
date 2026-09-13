"""Lightweight semantic lyric interpretation with no external API dependency."""

from __future__ import annotations

import re
from collections import Counter

STOPWORDS = {
    "the", "and", "a", "to", "i", "you", "it", "is", "in", "my", "me", "we", "our", "your", "of", "on",
    "for", "with", "that", "this", "but", "so", "be", "was", "are", "am", "yeah", "oh", "nah", "ayy", "got",
    "get", "like", "just", "dont", "can't", "cant", "i'm", "im", "do", "no", "not", "up", "down", "out",
}

THEME_LEXICON = {
    "romance": {"love", "girl", "boy", "baby", "kiss", "heart", "pretty", "beautiful", "mine", "touch", "lover"},
    "heartbreak": {"alone", "miss", "gone", "leave", "left", "cry", "hurt", "pain", "broken", "goodbye"},
    "nightlife": {"night", "club", "party", "lights", "dance", "drink", "city", "neon"},
    "success": {"money", "rich", "win", "winning", "top", "boss", "paid", "dream", "made", "success"},
    "motion": {"drive", "driving", "road", "car", "ride", "run", "running", "fly", "coast"},
    "reflection": {"mind", "remember", "memory", "think", "thinking", "dream", "past", "wonder"},
}

IMAGERY = {
    "romance": ["intimate close-up", "two figures separated by glass or reflections", "warm skin tones against cool surroundings"],
    "heartbreak": ["empty passenger seat", "subject alone in a large environment", "reflections and disappearing silhouettes"],
    "nightlife": ["neon-lit street or club", "moving city lights", "wet pavement reflections"],
    "success": ["confident performance framing", "premium architecture or vehicle", "low-angle hero shot"],
    "motion": ["night drive", "tracking shot beside a moving car", "fast foreground parallax"],
    "reflection": ["rear-view mirror imagery", "soft memory-like inserts", "double exposure or window reflection"],
}


def interpret_lyrics(lyrics: str) -> dict:
    text = (lyrics or "").strip()
    if not text:
        return {
            "themes": ["emotion", "performance"],
            "keywords": [],
            "emotion": "open-ended",
            "imagery": ["expressive artist close-up", "cinematic movement", "atmospheric environment"],
            "visual_metaphors": ["environment changes with the music"],
            "summary": "No lyrics supplied; prioritize the musical energy and artist performance.",
        }

    words = re.findall(r"[a-zA-Z']+", text.lower())
    content = [w for w in words if w not in STOPWORDS and len(w) > 2]
    counts = Counter(content)
    keywords = [w for w, _ in counts.most_common(10)]

    theme_scores = {theme: sum(counts[w] for w in lexicon) for theme, lexicon in THEME_LEXICON.items()}
    themes = [t for t, s in sorted(theme_scores.items(), key=lambda x: x[1], reverse=True) if s > 0][:3]
    if not themes:
        themes = ["reflection"]

    imagery = []
    for t in themes:
        imagery.extend(IMAGERY.get(t, []))
    # preserve order, remove duplicates
    imagery = list(dict.fromkeys(imagery))[:6]

    if "heartbreak" in themes:
        emotion = "longing and vulnerability"
    elif "romance" in themes:
        emotion = "attraction and intimacy"
    elif "success" in themes:
        emotion = "confidence and aspiration"
    elif "nightlife" in themes:
        emotion = "excitement and late-night energy"
    else:
        emotion = "introspection and momentum"

    metaphors = []
    if "reflection" in themes:
        metaphors.append("use mirrors, windows, or double exposure to suggest memory")
    if "heartbreak" in themes:
        metaphors.append("show absence through negative space or an empty seat")
    if "motion" in themes:
        metaphors.append("use travel and passing lights as a metaphor for emotional movement")
    if not metaphors:
        metaphors.append("let lighting and camera distance evolve with the musical intensity")

    return {
        "themes": themes,
        "keywords": keywords,
        "emotion": emotion,
        "imagery": imagery,
        "visual_metaphors": metaphors,
        "summary": f"Lyrics suggest {emotion}; center the visual language on {', '.join(themes)}.",
    }
