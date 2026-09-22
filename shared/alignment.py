from __future__ import annotations
import os,re,shutil,subprocess,sys,tempfile

def _tokens(s):return re.findall(r"[A-Za-z0-9']+",s or "")

def _separate_vocals(clip_path,workdir):
 """Return (audio_for_asr, status). Falls back to the mix on any Demucs error."""
 if os.environ.get("ENABLE_VOCAL_SEPARATION","1").lower() in {"0","false","no"}:
  return clip_path,"disabled"
 model=os.environ.get("DEMUCS_MODEL","htdemucs")
 out_dir=os.path.join(workdir,"demucs")
 cmd=[sys.executable,"-m","demucs.separate","--two-stems=vocals","-n",model,"-o",out_dir,clip_path]
 try:
  subprocess.run(cmd,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=600)
  stem=os.path.splitext(os.path.basename(clip_path))[0]
  vocals=os.path.join(out_dir,model,stem,"vocals.wav")
  if os.path.exists(vocals):return vocals,"separated"
  return clip_path,"fallback: vocals file not produced"
 except Exception as exc:
  return clip_path,f"fallback: {type(exc).__name__}"

def align_words(path,start,duration,supplied_lyrics=""):
 import whisperx,torch
 device="cuda" if torch.cuda.is_available() else "cpu";compute="float16" if device=="cuda" else "int8"
 # Trim first: all timestamps from WhisperX are local to the promo clip.
 workdir=tempfile.mkdtemp(prefix="map_transcribe_");tmp=os.path.join(workdir,"hook.wav")
 try:
  subprocess.run(["ffmpeg","-y","-loglevel","error","-ss",str(start),"-t",str(duration),"-i",path,"-ac","2","-ar","44100",tmp],check=True)
  asr_path,separation=_separate_vocals(tmp,workdir)
  audio=whisperx.load_audio(asr_path)
  language=os.environ.get("WHISPER_LANGUAGE","en")
  model_name=os.environ.get("WHISPER_MODEL","small")
  model=whisperx.load_model(model_name,device,compute_type=compute,language=language)
  result=model.transcribe(audio,batch_size=int(os.environ.get("WHISPER_BATCH_SIZE","4")))
  detected_language=result.get("language") or language
  align_model,metadata=whisperx.load_align_model(language_code=detected_language,device=device)
  aligned=whisperx.align(result["segments"],align_model,metadata,audio,device,return_char_alignments=False)
  raw=[{"word":w.get("word","").strip(),"start":float(w["start"]),"end":float(w["end"]),"score":float(w.get("score",0))} for w in aligned.get("word_segments",[]) if w.get("word") and "start" in w and "end" in w]
 finally:
  shutil.rmtree(workdir,ignore_errors=True)
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
 return raw,{"vocal_separation":separation,"language":detected_language,"model":model_name}
