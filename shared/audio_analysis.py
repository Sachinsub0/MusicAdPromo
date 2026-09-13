"""Music-aware, GPU-free analysis for short-form promo selection."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List

import librosa
import numpy as np


@dataclass
class SegmentScore:
    start: float
    end: float
    score: float
    energy: float
    onset_strength: float
    beat_density: float
    novelty: float
    reason: str

    def to_dict(self) -> dict:
        return asdict(self)


def _norm(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    if values.size == 0:
        return values
    lo, hi = float(np.min(values)), float(np.max(values))
    if hi - lo < 1e-9:
        return np.zeros_like(values)
    return (values - lo) / (hi - lo)


def analyze_audio(audio_path: str, clip_start: float = 0, clip_duration: float = 12) -> dict:
    """Summarize the selected moment for prompting and UI display."""
    y, sr = librosa.load(audio_path, offset=max(0, clip_start), duration=clip_duration)
    if y.size == 0:
        return {
            "tempo": 0.0,
            "rms": 0.0,
            "spectral_centroid": 0.0,
            "onset_strength": 0.0,
            "mood": "atmospheric",
            "brightness": "balanced",
            "energy": "moderate",
        }

    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    tempo = float(np.asarray(tempo).squeeze())
    rms = float(librosa.feature.rms(y=y).mean())
    centroid = float(librosa.feature.spectral_centroid(y=y, sr=sr).mean())
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    onset_strength = float(np.mean(onset_env)) if onset_env.size else 0.0

    if tempo >= 125:
        mood = "driving and urgent"
    elif tempo >= 95:
        mood = "confident and rhythmic"
    else:
        mood = "moody and atmospheric"

    if centroid >= 3000:
        brightness = "bright and vivid"
    elif centroid >= 1800:
        brightness = "balanced and cinematic"
    else:
        brightness = "dark and warm"

    if rms >= 0.10:
        energy = "explosive"
    elif rms >= 0.055:
        energy = "strong"
    else:
        energy = "restrained"

    return {
        "tempo": round(tempo, 2),
        "rms": round(rms, 5),
        "spectral_centroid": round(centroid, 2),
        "onset_strength": round(onset_strength, 4),
        "mood": mood,
        "brightness": brightness,
        "energy": energy,
    }


def rank_promo_segments(
    audio_path: str,
    clip_duration: int = 12,
    search_window: int | None = None,
    top_k: int = 5,
    step_seconds: float = 1.0,
) -> List[dict]:
    """
    Rank candidate 10–15s promo moments using multiple musical cues.

    v2 intentionally improves on "pick the loudest window" by combining:
      - RMS energy
      - onset activity (rhythmic events/transients)
      - beat density
      - local spectral novelty/change

    Lyrics are kept as a separate semantic signal because plain lyric text has
    no timestamps in the MVP. Timestamped transcription can be added later.
    """
    y, sr = librosa.load(audio_path, duration=search_window, mono=True)
    total_duration = len(y) / sr
    if total_duration <= clip_duration:
        return [SegmentScore(0, total_duration, 1.0, 1.0, 1.0, 1.0, 0.0, "Track is shorter than the promo window.").to_dict()]

    hop = 512
    rms = librosa.feature.rms(y=y, hop_length=hop)[0]
    onset = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=hop)[0]
    _, beat_frames = librosa.beat.beat_track(y=y, sr=sr, hop_length=hop)

    frame_step = hop / sr
    win = max(1, int(round(clip_duration / frame_step)))
    stride = max(1, int(round(step_seconds / frame_step)))

    starts = np.arange(0, max(1, len(rms) - win), stride)
    if starts.size == 0:
        starts = np.array([0])

    energy_vals, onset_vals, beat_vals, novelty_vals = [], [], [], []
    beat_set = np.asarray(beat_frames)

    for s in starts:
        e = min(len(rms), s + win)
        energy_vals.append(float(np.mean(rms[s:e])))
        onset_vals.append(float(np.mean(onset[s:min(len(onset), e)])))
        beat_vals.append(float(np.sum((beat_set >= s) & (beat_set < e))) / max(clip_duration, 1))

        c = centroid[s:min(len(centroid), e)]
        if len(c) > 1:
            novelty_vals.append(float(np.mean(np.abs(np.diff(c)))))
        else:
            novelty_vals.append(0.0)

    en = _norm(np.array(energy_vals))
    on = _norm(np.array(onset_vals))
    bd = _norm(np.array(beat_vals))
    nv = _norm(np.array(novelty_vals))

    # Promotion-oriented starting weights. Easy to tune later from user data.
    scores = 0.42 * en + 0.28 * on + 0.18 * bd + 0.12 * nv

    # Greedy non-max suppression so top results are meaningfully different.
    order = list(np.argsort(scores)[::-1])
    chosen = []
    min_separation = max(clip_duration * 0.6, 4)
    for idx in order:
        start_sec = float(starts[idx] * frame_step)
        if any(abs(start_sec - c[0]) < min_separation for c in chosen):
            continue
        chosen.append((start_sec, idx))
        if len(chosen) >= top_k:
            break

    results: List[dict] = []
    for start_sec, idx in chosen:
        end_sec = min(total_duration, start_sec + clip_duration)
        strongest = sorted(
            [(en[idx], "high sustained energy"), (on[idx], "strong rhythmic/onset activity"), (bd[idx], "dense beat activity"), (nv[idx], "noticeable timbral change")],
            reverse=True,
        )[:2]
        reason = " + ".join(x[1] for x in strongest)
        results.append(
            SegmentScore(
                start=round(start_sec, 2),
                end=round(end_sec, 2),
                score=round(float(scores[idx]), 4),
                energy=round(float(en[idx]), 4),
                onset_strength=round(float(on[idx]), 4),
                beat_density=round(float(bd[idx]), 4),
                novelty=round(float(nv[idx]), 4),
                reason=reason,
            ).to_dict()
        )
    return results


def find_best_clip_start(audio_path: str, clip_duration: int = 12, search_window: int | None = None) -> int:
    ranked = rank_promo_segments(audio_path, clip_duration, search_window, top_k=1)
    return int(round(ranked[0]["start"])) if ranked else 0


def suggested_cut_points(audio_path: str, clip_start: float, clip_duration: float, max_shots: int = 3) -> List[float]:
    """Return beat/onset-aware relative cut points inside the selected promo."""
    y, sr = librosa.load(audio_path, offset=clip_start, duration=clip_duration, mono=True)
    if y.size == 0 or max_shots <= 1:
        return [0.0, float(clip_duration)]

    hop = 512
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
    onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, hop_length=hop, backtrack=True)
    onset_times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=hop)

    targets = [clip_duration * i / max_shots for i in range(1, max_shots)]
    cuts = [0.0]
    for target in targets:
        valid = onset_times[(onset_times > target - 1.1) & (onset_times < target + 1.1)]
        if valid.size:
            chosen = float(valid[np.argmin(np.abs(valid - target))])
        else:
            chosen = float(target)
        if chosen - cuts[-1] >= 1.5:
            cuts.append(round(chosen, 2))
    cuts.append(float(clip_duration))
    return cuts
