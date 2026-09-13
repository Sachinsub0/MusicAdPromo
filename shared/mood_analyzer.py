"""Audio + lyric mood analysis for the simplified MusicAdPromo v4 pipeline."""
from __future__ import annotations
import re
import numpy as np
import librosa

POS = {"love","pretty","beautiful","baby","dance","party","good","smile","kiss","touch","alive","happy","tonight","dream"}
NEG = {"alone","lonely","miss","cry","pain","hurt","lost","gone","dark","cold","broken","sad","hate","die","dead"}
DARK = {"night","dark","shadow","black","ghost","blood","devil","cold","empty","alone"}
ROMANCE = {"love","baby","girl","boy","kiss","touch","heart","pretty","face","mine","you","us","together"}
MOTION = {"drive","car","road","run","dance","fly","ride","city","club","street","ocean","coast"}

def _words(text: str):
    return re.findall(r"[a-zA-Z']+", (text or "").lower())

def analyze_song_mood(audio_path: str, lyrics: str, clip_start: float, clip_duration: float) -> dict:
    y, sr = librosa.load(audio_path, sr=22050, mono=True, offset=max(0,float(clip_start)), duration=float(clip_duration))
    if len(y) == 0:
        raise ValueError("Could not decode selected audio.")
    rms = librosa.feature.rms(y=y)[0]
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    onset = librosa.onset.onset_strength(y=y, sr=sr)
    tempo = float(librosa.feature.tempo(onset_envelope=onset, sr=sr, aggregate=np.median)[0])
    energy = float(np.clip(np.mean(rms) / 0.16, 0, 1))
    brightness = float(np.clip(np.mean(centroid) / 4500.0, 0, 1))
    pulse = float(np.clip(np.std(onset) / 2.5, 0, 1))
    words = _words(lyrics)
    pos = sum(w in POS for w in words); neg = sum(w in NEG for w in words)
    romantic = sum(w in ROMANCE for w in words)
    dark = sum(w in DARK for w in words)
    motion = sum(w in MOTION for w in words)
    valence = 0.5 if pos+neg == 0 else float(np.clip(0.5 + (pos-neg)/(2*(pos+neg)),0,1))
    if romantic >= 2 and valence < .6: labels = ["romantic","longing","dreamy"]
    elif dark >= 2 or valence < .3: labels = ["dark","melancholic","cinematic"]
    elif energy > .72 and pulse > .35: labels = ["energetic","confident","kinetic"]
    elif valence > .68: labels = ["uplifting","warm","bright"]
    else: labels = ["moody","intimate","cinematic"]
    movement = "slow, fluid, restrained" if energy < .45 else ("smooth, confident, medium-paced" if energy < .72 else "energetic, rhythmic, responsive")
    return {
        "tempo_bpm": round(tempo,1), "energy": round(energy,2), "brightness": round(brightness,2),
        "rhythmic_activity": round(pulse,2), "valence": round(valence,2),
        "mood_labels": labels, "movement_style": movement,
        "lyric_signals": {"romance": romantic, "darkness": dark, "motion": motion}
    }

def analyze_lyrics(lyrics: str) -> dict:
    lines = [re.sub(r"\s+"," ",x).strip() for x in (lyrics or "").splitlines() if x.strip()]
    words = _words(lyrics)
    if not words:
        return {"theme":"instrumental / mood-led","summary":"No lyrics supplied; the visual should follow the music rather than a literal narrative.","key_lyric":"","imagery":["light","texture","motion"]}
    romance=sum(w in ROMANCE for w in words); dark=sum(w in DARK for w in words); motion=sum(w in MOTION for w in words)
    neg=sum(w in NEG for w in words)
    if romance>=2 and neg>=1: theme="romantic longing"
    elif romance>=2: theme="attraction / romance"
    elif dark>=2: theme="isolation / darkness"
    elif motion>=2: theme="movement / nightlife"
    else: theme="self-expression / atmosphere"
    # Prefer a short, repeated line as the on-screen lyric.
    counts={}
    for line in lines:
        key=line.lower()
        counts[key]=counts.get(key,0)+1
    ranked=sorted(lines, key=lambda x:(counts.get(x.lower(),1), -abs(len(x)-35)), reverse=True)
    key_lyric=(ranked[0][:90] if ranked else "")
    imagery=[]
    if motion: imagery += ["moving lights","road or city motion"]
    if dark: imagery += ["night","shadows","reflections"]
    if romance: imagery += ["intimate portrait","presence or absence of another person"]
    if not imagery: imagery=["cinematic portrait","environmental light","abstract texture"]
    return {"theme":theme,"summary":f"The lyrics center on {theme}, so the visual should communicate that feeling without acting out every line.","key_lyric":key_lyric,"imagery":imagery[:4]}
