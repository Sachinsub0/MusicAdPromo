import os,tempfile
from fastapi import FastAPI,UploadFile,File,Form,HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from shared.audio import load_audio,propose_hooks,clip_audio,wav_bytes
from shared.alignment_v7 import align_clip,validate_words

app=FastAPI(title='MusicAdPromo v7 API')
MAX_BYTES=30*1024*1024

async def receive(audio):
    data=await audio.read(MAX_BYTES+1)
    if len(data)>MAX_BYTES:raise HTTPException(413,'Audio file exceeds 30MB')
    try:return load_audio(data)
    except Exception as e:raise HTTPException(422,f'Unable to decode audio: {e}')

@app.get('/health')
def health():return {'status':'ok','version':'7-starter'}

@app.post('/v7/hooks')
async def hooks(audio:UploadFile=File(...),duration:int=Form(15)):
    if not 10<=duration<=25:raise HTTPException(422,'Duration must be 10–25 seconds')
    y,sr=await receive(audio)
    try:choices=propose_hooks(y,sr,duration)
    except ValueError as e:raise HTTPException(422,str(e))
    return {'duration':round(len(y)/sr,2),'hooks':choices,'method':'RMS + onset heuristic'}

@app.post('/v7/preview')
async def preview(audio:UploadFile=File(...),start:float=Form(...),duration:int=Form(15)):
    y,sr=await receive(audio)
    try:segment=clip_audio(y,sr,start,duration)
    except ValueError as e:raise HTTPException(422,str(e))
    return Response(wav_bytes(segment,sr),media_type='audio/wav')

@app.post('/v7/align')
async def align(audio:UploadFile=File(...),start:float=Form(...),duration:int=Form(15),lyrics:str=Form(''),language:str=Form('')):
    y,sr=await receive(audio)
    try:segment=clip_audio(y,sr,start,duration)
    except ValueError as e:raise HTTPException(422,str(e))
    with tempfile.NamedTemporaryFile(suffix='.wav',delete=False) as f:
        f.write(wav_bytes(segment,sr));path=f.name
    try:return align_clip(path,lyrics,language)
    except RuntimeError as e:raise HTTPException(503,str(e))
    finally:os.unlink(path)

class TimingPayload(BaseModel):
    duration:float
    words:list[dict]

@app.post('/v7/validate-timings')
def validate_timings(payload:TimingPayload):
    try:return {'words':validate_words(payload.words,payload.duration)}
    except (ValueError,KeyError,TypeError) as e:raise HTTPException(422,str(e))
