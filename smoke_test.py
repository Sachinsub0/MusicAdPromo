"""CPU-only smoke test for v3A planning. No network/GPU required."""

from __future__ import annotations

import os
import tempfile
import wave

import numpy as np

from shared.prompt_builder import create_creative_plan, rank_promo_segments


def write_test_wav(path: str, sr: int = 22050, seconds: int = 24):
    t = np.arange(sr * seconds) / sr
    # Quiet first half, stronger rhythmic second half to give the ranker something obvious.
    y = 0.02 * np.sin(2 * np.pi * 220 * t)
    mask = t >= 10
    y[mask] += 0.18 * np.sin(2 * np.pi * 110 * t[mask])
    beat = ((t * 2) % 1.0) < 0.06
    y[mask & beat] += 0.35
    y = np.clip(y, -1, 1)
    pcm = (y * 32767).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())


def main():
    fd, path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    try:
        write_test_wav(path)
        ranked = rank_promo_segments(path, clip_duration=10, top_k=3)
        assert ranked, "No hook candidates returned"
        plan = create_creative_plan(
            path,
            lyrics="pretty face, driving at night, can't get you off my mind",
            genre="Hip Hop",
            visual_style="Dark Cinematic",
            clip_start=ranked[0]["start"],
            clip_duration=10,
            max_shots=3,
        )
        assert len(plan["shots"]) >= 2
        for shot in plan["shots"]:
            assert shot["keyframe_prompt"]
            assert shot["motion_prompt"]
        print("PASS: MusicAdPromo v3A CPU planning smoke test")
        print("Top hook:", ranked[0])
        print("Concept:", plan["concept"])
        for shot in plan["shots"]:
            print(f"Shot {shot['index']}: {shot['start']}–{shot['end']}s | {shot['description']}")
    finally:
        os.remove(path)


if __name__ == "__main__":
    main()
