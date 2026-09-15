from __future__ import annotations
import os,re,tempfile,subprocess
def _tokens(s):return re.findall(r"[A-Za-z0-9']+",s or "")
def align_words(path,start,duration,supplied_lyrics=""):
 import whisperx,torch
 device="cuda" if torch.cuda.is_available() else "cpu";compute="float16" if device=="cuda" else "int8"
 # Trim first: all timestamps from WhisperX are local to the promo clip.
 tmp=tempfile.NamedTemporaryFile(suffix=".wav",delete=False).name
 subprocess.run(["ffmpeg","-y","-loglevel","error","-ss",str(start),"-t",str(duration),"-i",path,"-ac","1","-ar","16000",tmp],check=True)
 audio=whisperx.load_audio(tmp)
 model=whisperx.load_model("small",device,compute_type=compute,language="en")
 result=model.transcribe(audio,batch_size=4)
 align_model,metadata=whisperx.load_align_model(language_code=result["language"],device=device)
 aligned=whisperx.align(result["segments"],align_model,metadata,audio,device,return_char_alignments=False)
 raw=[{"word":w.get("word","").strip(),"start":float(w["start"]),"end":float(w["end"]),"score":float(w.get("score",0))} for w in aligned.get("word_segments",[]) if w.get("word") and "start" in w and "end" in w]
 try:os.unlink(tmp)
 except:pass
 # Keep WhisperX timing sacred. Supplied lyrics are used only to correct spelling sequentially when token counts are plausible.
 target=_tokens(supplied_lyrics)
 if target and raw:
  # locate best target window against aligned transcript
  import difflib
  rw=[re.sub(r"\W","",x["word"].lower()) for x in raw]; tw=[x.lower() for x in target]; n=len(rw);best=(0,-1.)
  for i in range(max(1,len(tw)-n+1)):
   sc=difflib.SequenceMatcher(None," ".join(tw[i:i+n])," ".join(rw)).ratio()
   if sc>best[1]:best=(i,sc)
  cand=target[best[0]:best[0]+n]
  if len(cand)==len(raw) and best[1]>.35:
   for w,t in zip(raw,cand):w["word"]=t
 return raw
