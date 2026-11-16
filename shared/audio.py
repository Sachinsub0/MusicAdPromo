import io
import numpy as np
import soundfile as sf
import librosa

def load_audio(data: bytes):
    try:
        y, sr = sf.read(io.BytesIO(data), always_2d=True)
        return y.mean(axis=1).astype(np.float32), sr
    except Exception:
        import tempfile, os
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            f.write(data); path=f.name
        try:
            y,sr=librosa.load(path,sr=None,mono=True)
            return y,sr
        finally: os.unlink(path)

def propose_hooks(y, sr, duration=15, count=5):
    total=len(y)/sr
    if total < duration: raise ValueError('Song is shorter than the requested video duration')
    hop=512
    # RMS + onset strength yield a transparent, deterministic ranking (not a trained hook model).
    rms=librosa.feature.rms(y=y,hop_length=hop)[0]
    onset=librosa.onset.onset_strength(y=y,sr=sr,hop_length=hop)
    n=min(len(rms),len(onset)); rms=rms[:n]; onset=onset[:n]
    rms=rms/(np.max(rms)+1e-8); onset=onset/(np.max(onset)+1e-8)
    activity=.6*rms+.4*onset
    step=max(1,int(2*sr/hop)); win=max(1,int(duration*sr/hop))
    candidates=[]
    for i in range(0,max(1,n-win+1),step):
        start=i*hop/sr
        if start+duration > total: continue
        score=float(np.mean(activity[i:i+win]))
        candidates.append((score,start))
    candidates.sort(reverse=True)
    selected=[]
    for score,start in candidates:
        if all(abs(start-prev['start'])>=duration*.6 for prev in selected):
            selected.append({'start':round(start,2),'end':round(start+duration,2),'score':round(score,3)})
        if len(selected)==count: break
    # Very short songs may not fit five non-overlapping candidates: fill with spaced alternatives.
    if len(selected)<count:
        for start in np.linspace(0,total-duration,count*3):
            if all(abs(start-prev['start'])>0.5 for prev in selected):
                selected.append({'start':round(float(start),2),'end':round(float(start+duration),2),'score':None})
            if len(selected)==count: break
    return selected

def clip_audio(y,sr,start,duration):
    if start<0 or duration<10 or duration>25 or start+duration>len(y)/sr+0.01:
        raise ValueError('Invalid selection: choose 10–25 seconds within the song')
    return y[round(start*sr):round((start+duration)*sr)]

def wav_bytes(y,sr):
    b=io.BytesIO();sf.write(b,y,sr,format='WAV',subtype='PCM_16');return b.getvalue()
