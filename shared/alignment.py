from __future__ import annotations
import os,re,shutil,subprocess,sys,tempfile

def _tokens(s):return (s or "").split()

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
  # Corrections are the actual alignment transcript, including insertions/deletions.
  segments=result["segments"]
  if supplied_lyrics.strip():
   segments=[{"start":0.0,"end":float(duration),"text":supplied_lyrics.strip()}]
  aligned=whisperx.align(segments,align_model,metadata,audio,device,return_char_alignments=False)
  text=supplied_lyrics.strip() or " ".join(x.get("text", "").strip() for x in segments)
  raw=complete_words(text,aligned.get("word_segments",[]),duration)
 finally:
  shutil.rmtree(workdir,ignore_errors=True)
 return raw,{"vocal_separation":separation,"language":detected_language,"model":model_name,
             "timing_estimated":sum(w.get("estimated",False) for w in raw)}


def complete_words(text, aligned, duration):
 """Keep every transcript token, filling missing ASR timestamps explicitly."""
 tokens=_tokens(text)
 # WhisperX preserves word order, including untimed words.
 from difflib import SequenceMatcher
 norm=lambda x: re.sub(r"\W", "", x.casefold())
 rows=[{"word":t,"estimated":True,"score":0.0} for t in tokens]
 matches=SequenceMatcher(None,[norm(t) for t in tokens],[norm(w.get("word","")) for w in aligned],autojunk=False)
 for block in matches.get_matching_blocks():
  for i,j in zip(range(block.a,block.a+block.size),range(block.b,block.b+block.size)):
   w=aligned[j]
   if w.get("start") is not None and w.get("end") is not None:
    start=max(0.0,min(float(duration),float(w["start"])))
    end=max(start,min(float(duration),float(w["end"])))
    rows[i].update(start=start,end=end,score=float(w.get("score") or 0),estimated=bool(w.get("estimated",False)))
 # Reject backwards anchors, then interpolate only the missing spans.
 last=0.0
 for row in rows:
  if "start" in row:
   if row["start"]<last:row.pop("start");row.pop("end");row["estimated"]=True
   else:last=row["end"]
 i=0
 while i<len(rows):
  if "start" in rows[i]:i+=1;continue
  j=i
  while j<len(rows) and "start" not in rows[j]:j+=1
  left=rows[i-1]["end"] if i else 0.0
  right=rows[j]["start"] if j<len(rows) else float(duration)
  step=max(0.0,right-left)/(j-i)
  for k in range(i,j):rows[k].update(start=left+(k-i)*step,end=left+(k-i+1)*step)
  i=j
 return rows


def preview_corrections(words, text, duration):
 """Reuse unchanged anchors; label changed spans as provisional until forced alignment."""
 return complete_words(text,words,duration)
