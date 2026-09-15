from __future__ import annotations
import librosa,numpy as np
def rank_hooks(path,duration=12,top_k=5):
 y,sr=librosa.load(path,sr=22050,mono=True);hop=512;rms=librosa.feature.rms(y=y,hop_length=hop)[0];oe=librosa.onset.onset_strength(y=y,sr=sr,hop_length=hop);win=max(1,int(duration*sr/hop))
 def roll(x):return np.array([x.mean()]) if len(x)<win else np.convolve(x,np.ones(win)/win,mode="valid")
 def norm(x):return (x-x.min())/(x.max()-x.min()+1e-9)
 score=.55*norm(roll(rms))+.45*norm(roll(oe));out=[]
 for i in np.argsort(score)[::-1]:
  s=float(i*hop/sr)
  if all(abs(s-x["start"])>duration*.65 for x in out):out.append({"start":round(s,3),"end":round(s+duration,3),"score":round(float(score[i]),3)})
  if len(out)>=top_k:break
 return out
def timeline(path,start,duration):
 y,sr=librosa.load(path,sr=22050,mono=True,offset=start,duration=duration);hop=256
 oe=librosa.onset.onset_strength(y=y,sr=sr,hop_length=hop)
 tempo,beats=librosa.beat.beat_track(onset_envelope=oe,sr=sr,hop_length=hop,units="time",trim=False)
 ons=librosa.onset.onset_detect(onset_envelope=oe,sr=sr,hop_length=hop,units="time",backtrack=False)
 # strong onsets only
 frames=librosa.time_to_frames(ons,sr=sr,hop_length=hop);strength=oe[np.clip(frames,0,len(oe)-1)] if len(frames) else np.array([])
 threshold=np.quantile(strength,.65) if len(strength) else 0
 strong=[float(t) for t,v in zip(ons,strength) if v>=threshold]
 rms=librosa.feature.rms(y=y,hop_length=hop)[0];cent=librosa.feature.spectral_centroid(y=y,sr=sr,hop_length=hop)[0]
 return {"tempo_bpm":round(float(np.asarray(tempo).reshape(-1)[0]),2),"beats":[round(float(x),4) for x in beats],"onsets":[round(x,4) for x in strong],
 "energy":round(float(np.clip(rms.mean()/.16,0,1)),2),"brightness":round(float(np.clip(cent.mean()/4500,0,1)),2)}
