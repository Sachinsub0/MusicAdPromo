"""MusicAdPromo v4 API — one visual, mood/lyrics aware, image-to-video."""
from __future__ import annotations
import json, os, sys, uuid
import modal
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import JSONResponse
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.audio_analysis import rank_promo_segments
from shared.mood_analyzer import analyze_song_mood, analyze_lyrics
from shared.visual_director import direct_visual
from shared.storyboard import NEGATIVE_PROMPT
from storage import get_download_url, upload_audio
load_dotenv()
app=FastAPI(title="MusicAdPromo v4")
image_fn=modal.Function.from_name("musicadpromo-v4","generate_hero_image")
video_fn=modal.Function.from_name("musicadpromo-v4","animate_promo")

def _tmp(audio,data):
    ext=os.path.splitext(audio.filename or "audio.wav")[1] or ".wav"
    p=f"/tmp/{uuid.uuid4().hex}{ext}"; open(p,"wb").write(data); return p

@app.get("/health")
def health(): return {"status":"ok","version":"MusicAdPromo-v4","mode":"single-visual"}

@app.post("/analyze")
async def analyze(audio:UploadFile=File(...), lyrics:str=Form(""), genre:str=Form("Hip Hop"),
                  clip_duration:int=Form(12), selected_start:float|None=Form(None), visual_direction:str=Form("")):
    raw=await audio.read(); p=_tmp(audio,raw)
    try:
        candidates=rank_promo_segments(p,clip_duration=clip_duration,top_k=5)
        start=float(selected_start if selected_start is not None else (candidates[0]["start"] if candidates else 0))
        mood=analyze_song_mood(p,lyrics,start,clip_duration)
        lyric=analyze_lyrics(lyrics)
        visual=direct_visual(mood,lyric,genre,visual_direction)
        return {"candidates":candidates,"clip_start":start,"clip_duration":clip_duration,"mood":mood,"lyrics":lyric,"visual":visual}
    finally:
        try: os.remove(p)
        except OSError: pass

@app.post("/generate-image")
async def generate_image(analysis_json:str=Form(...), platform:str=Form("TikTok / Reels (9:16)"),
                         seed:int=Form(42), quality_mode:str=Form("better"), custom_prompt:str=Form("")):
    a=json.loads(analysis_json); prompt=custom_prompt.strip() or a["visual"]["image_prompt"]
    call=image_fn.spawn(prompt=prompt,negative_prompt=NEGATIVE_PROMPT,platform=platform,seed=int(seed),quality_mode=quality_mode)
    return {"job_id":call.object_id,"prompt":prompt}

@app.post("/generate-video")
async def generate_video(audio:UploadFile=File(...), analysis_json:str=Form(...), image_object_key:str=Form(...),
                         platform:str=Form("TikTok / Reels (9:16)"), quality_mode:str=Form("fast"),
                         seed:int=Form(42), custom_motion_prompt:str=Form("")):
    a=json.loads(analysis_json); raw=await audio.read(); p=_tmp(audio,raw)
    try:
        key=upload_audio(p,uuid.uuid4().hex,content_type=audio.content_type or "audio/mpeg")
    finally:
        try: os.remove(p)
        except OSError: pass
    motion=custom_motion_prompt.strip() or a["visual"]["motion_prompt"]
    call=video_fn.spawn(image_object_key=image_object_key,audio_key=key,clip_start=float(a["clip_start"]),
                        clip_duration=float(a["clip_duration"]),motion_prompt=motion,platform=platform,
                        quality_mode=quality_mode,seed=int(seed),key_lyric=a["lyrics"].get("key_lyric",""))
    return {"job_id":call.object_id}

@app.get("/status/{job_id}")
async def status(job_id:str):
    call=modal.FunctionCall.from_id(job_id)
    try: r=call.get(timeout=0)
    except TimeoutError: return {"status":"processing"}
    except Exception as e: return JSONResponse(status_code=500,content={"status":"failed","error":str(e)})
    try: url=get_download_url(r["object_key"])
    except Exception as e: return JSONResponse(status_code=500,content={"status":"failed","error":str(e)})
    return {"status": "done", "artifact_type": r["type"], "url": url, "object_key": r["object_key"], **{k:v for k,v in r.items() if k not in ["object_key", "type"]}}
