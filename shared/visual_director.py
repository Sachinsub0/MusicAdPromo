"""Single-visual creative direction for MusicAdPromo v4."""
from __future__ import annotations

def direct_visual(mood: dict, lyric: dict, genre: str, user_direction: str="") -> dict:
    labels=", ".join(mood["mood_labels"])
    theme=lyric["theme"]
    if user_direction.strip():
        concept=user_direction.strip()
    elif "romantic" in labels or "longing" in labels:
        concept="A solitary cinematic portrait at night, with moving city reflections and an intentional sense that someone important is absent."
    elif "energetic" in labels:
        concept="A bold performance portrait in a striking night environment, with strong depth, practical lights and immediate attitude."
    elif "dark" in labels or "melancholic" in labels:
        concept="An intimate low-light portrait surrounded by shadows, reflections and distant practical lights, emotionally restrained rather than literal."
    else:
        concept="A polished artist portrait in a visually distinctive environment whose lighting and texture mirror the song's mood."
    image_prompt=(
        f"Vertical 9:16 premium music-promo hero frame. {concept} "
        f"Music mood: {labels}. Lyric theme: {theme}. Genre: {genre}. "
        "One clear focal subject, simple composition, cinematic practical lighting, believable depth, tasteful color contrast, "
        "high-end editorial music photography, realistic anatomy, no text, no logos, no collage, no split screen. "
        "Leave some clean negative space for optional lyric typography."
    )
    motion_prompt=(
        f"Preserve the exact subject, face, wardrobe, environment and composition. "
        f"Animate with {mood['movement_style']} motion: a subtle cinematic camera push or parallax, natural breathing and micro-movement, "
        "gentle environmental motion and moving light/reflections. No scene change, no morphing, no new people, no cuts, "
        "no dramatic body movement, no camera teleportation. Create a seamless premium animated-cover-art feeling."
    )
    return {"concept":concept,"image_prompt":image_prompt,"motion_prompt":motion_prompt}
