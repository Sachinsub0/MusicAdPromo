from __future__ import annotations
import os,sys,tempfile,uuid,json
from fastapi import FastAPI,UploadFile,File,Form
from fastapi.responses import FileResponse
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.audio import rank_hooks,timeline
from shared.alignment import align_words
from shared.director import understand,decorate,image_prompt
from shared.renderer import render
app=FastAPI(title="MusicAdPromo v6");OUT=os.path.join(tempfile.gettempdir(),"mapv6");os.makedirs(OUT,exist_ok=True)
def save(u,b):
 ext=os.path.splitext(u.filename or "x")[1] or ".bin";p=os.path.join(OUT,uuid.uuid4().hex+ext);open(p,"wb").write(b);return p
@app.get("/health")
def health():return {"status":"ok","version":"MusicAdPromo-v6.2-auto-lyrics"}
@app.post("/analyze")
async def analyze(audio:UploadFile=File(...),lyrics:str=Form(""),duration:int=Form(12),selected_start:float|None=Form(None)):
 raw=await audio.read();p=save(audio,raw);c=rank_hooks(p,duration);start=float(selected_start if selected_start is not None else c[0]["start"]);tl=timeline(p,start,duration)
 words,transcription=align_words(p,start,duration,lyrics)
 detected_lyrics=" ".join(w["word"] for w in words)
 effective_lyrics=lyrics.strip() or detected_lyrics
 creative=understand(effective_lyrics,tl);words=decorate(words,tl)
 return {"clip_start":start,"duration":duration,"candidates":c,"timeline":tl,"creative":creative,"words":words,"detected_lyrics":detected_lyrics,"transcription":transcription,"image_prompt":image_prompt(creative)}
@app.post("/render")
async def make(audio:UploadFile=File(...),plan_json:str=Form(...),background:UploadFile|None=File(None)):
 ap=save(audio,await audio.read());bp=None
 if background:bp=save(background,await background.read())
 plan=json.loads(plan_json);out=os.path.join(OUT,uuid.uuid4().hex+".mp4");render(plan,ap,out,bp);return {"video_id":os.path.basename(out)}
@app.get("/video/{vid}")
def vid(vid:str):return FileResponse(os.path.join(OUT,os.path.basename(vid)),media_type="video/mp4",filename="musicadpromo-v6.mp4")
