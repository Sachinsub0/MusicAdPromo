"""Storyboard prompt construction and lightweight image quality checks for MusicAdPromo v3A."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

import numpy as np
from PIL import Image, ImageStat

PLATFORM_RESOLUTIONS = {
    "TikTok / Reels (9:16)": (576, 1024),
    "Square (1:1)": (768, 768),
    "Landscape (16:9)": (1024, 576),
}
DEFAULT_PLATFORM = "TikTok / Reels (9:16)"

NEGATIVE_PROMPT = (
    "text, captions, watermark, logo, UI, split screen, collage, duplicate person, extra limbs, "
    "extra fingers, malformed hands, distorted face, crossed eyes, low resolution, blurry, muddy, "
    "flat lighting, overexposed, underexposed, empty frame, random objects, deformed anatomy"
)


@dataclass
class QualityReport:
    passed: bool
    mean_luma: float
    contrast: float
    entropy: float
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_keyframe_prompt(plan: dict, shot: dict) -> str:
    lyrics = plan.get("lyrics", {})
    music = plan.get("music", {})
    return (
        f"Single cinematic music-video keyframe, not a poster and no text. {shot['role']}. "
        f"Scene: {shot['description']}. Composition: {shot['composition']}. "
        f"Character direction: {shot['character_direction']}. "
        f"Location and continuity: {shot['continuity']}. "
        f"Visual style: {plan['style']}. Color direction: {plan['palette']}. "
        f"Emotion: {lyrics.get('emotion', 'expressive')}. Music feel: {music.get('mood', 'rhythmic')}. "
        "Professional music-video cinematography, realistic depth, intentional lighting, clean subject separation, "
        "strong foreground/midground/background layering, coherent anatomy, believable environment, premium editorial finish."
    )


def build_motion_prompt(plan: dict, shot: dict) -> str:
    return (
        f"Preserve the exact subject identity, wardrobe, composition, lighting and environment from the keyframe. "
        f"Camera motion: {shot['camera']}. Subject motion: {shot['motion']}. "
        "Use subtle realistic movement, stable anatomy, stable face, natural cloth/hair motion, no scene replacement, "
        "no sudden zooms, no morphing, no new characters, no text."
    )


def validate_image(image: Image.Image) -> QualityReport:
    """Catch catastrophic generations (black/blank/near-uniform) without rejecting intentionally dark art."""
    rgb = image.convert("RGB")
    gray = rgb.convert("L")
    arr = np.asarray(gray, dtype=np.float32)
    mean_luma = float(arr.mean())
    contrast = float(arr.std())
    hist = np.asarray(gray.histogram(), dtype=np.float64)
    p = hist / max(hist.sum(), 1.0)
    p = p[p > 0]
    entropy = float(-(p * np.log2(p)).sum())

    passed = True
    reason = "ok"
    if mean_luma < 3.0 and contrast < 4.0:
        passed, reason = False, "near-black frame"
    elif mean_luma > 252.0 and contrast < 3.0:
        passed, reason = False, "near-white frame"
    elif contrast < 2.0:
        passed, reason = False, "near-uniform frame"
    elif entropy < 1.5:
        passed, reason = False, "very low visual information"

    return QualityReport(
        passed=passed,
        mean_luma=round(mean_luma, 2),
        contrast=round(contrast, 2),
        entropy=round(entropy, 3),
        reason=reason,
    )
