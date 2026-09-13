"""Modal workers for MusicAdPromo v4."""
from __future__ import annotations
import modal
app=modal.App("musicadpromo-v4")

PLATFORM_RESOLUTIONS = {
    "TikTok / Reels (9:16)": (576, 1024),
    "Square (1:1)": (768, 768),
    "Landscape (16:9)": (1024, 576),
}
DEFAULT_PLATFORM = "TikTok / Reels (9:16)"

def _r2_client():
    import os, boto3
    from botocore.config import Config
    account_id = os.environ["R2_ACCOUNT_ID"]
    return boto3.client(
        "s3",
        endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )

def _bucket():
    import os
    return os.environ["R2_BUCKET_NAME"]

def _upload_image(local_path, job_id):
    key = f"images/{job_id}.png"
    _r2_client().upload_file(local_path, _bucket(), key, ExtraArgs={"ContentType":"image/png"})
    return key

def _upload_video(local_path, job_id):
    key = f"videos/{job_id}.mp4"
    _r2_client().upload_file(local_path, _bucket(), key, ExtraArgs={"ContentType":"video/mp4"})
    return key

def _download_object(key, local_path):
    _r2_client().download_file(_bucket(), key, local_path)
    return local_path

def _validate_image(im):
    import numpy as np
    arr = np.asarray(im.convert("L"), dtype=np.float32)
    mean = float(arr.mean())
    contrast = float(arr.std())
    hist, _ = np.histogram(arr, bins=256, range=(0,255), density=True)
    hist = hist[hist > 0]
    entropy = float(-(hist * np.log2(hist)).sum())
    passed = not ((mean < 3 and contrast < 4) or (mean > 252 and contrast < 3) or contrast < 2 or entropy < 1.5)
    return {"passed": passed, "mean_luma": round(mean,2), "contrast": round(contrast,2), "entropy": round(entropy,2)}
image=(modal.Image.debian_slim(python_version="3.11").apt_install("ffmpeg").pip_install(
    "torch","diffusers>=0.35.0","transformers","accelerate","safetensors","sentencepiece",
    "numpy","pillow>=10.0.0","boto3","imageio","imageio-ffmpeg"
))
secret=modal.Secret.from_name("r2-credentials")

def _run(cmd):
    import subprocess
    p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    if p.returncode: raise RuntimeError(p.stderr[-5000:])

def _quality(path):
    import os,tempfile,numpy as np
    from PIL import Image
    d=tempfile.mkdtemp(); pat=os.path.join(d,"f_%02d.jpg")
    _run(["ffmpeg","-y","-loglevel","error","-i",path,"-vf","fps=1","-frames:v","6",pat])
    ps=sorted(os.path.join(d,x) for x in os.listdir(d) if x.endswith(".jpg"))
    if len(ps)<2:return {"passed":False,"reason":"not enough frames"}
    fs=[np.asarray(Image.open(x).convert("L"),dtype=np.float32) for x in ps]
    lum=float(np.mean([x.mean() for x in fs])); con=float(np.mean([x.std() for x in fs]))
    dif=float(np.mean([np.mean(np.abs(fs[i]-fs[i-1])) for i in range(1,len(fs))]))
    ok=lum>=4 and con>=2 and dif>=.2
    return {"passed":ok,"mean_luma":round(lum,2),"mean_contrast":round(con,2),"temporal_change":round(dif,3)}

@app.function(image=image,gpu="A10G",timeout=1200,secrets=[secret])
def generate_hero_image(prompt:str,negative_prompt:str,platform:str,seed:int,quality_mode:str="better"):
    import os,uuid,torch
    from diffusers import AutoPipelineForText2Image
    
    model=os.environ.get("HERO_IMAGE_MODEL","stabilityai/sdxl-turbo")
    w,h=PLATFORM_RESOLUTIONS.get(platform,PLATFORM_RESOLUTIONS[DEFAULT_PLATFORM])
    steps={"fast":2,"better":4,"best":6}.get(quality_mode,4)
    pipe=AutoPipelineForText2Image.from_pretrained(model,torch_dtype=torch.float16,variant="fp16",low_cpu_mem_usage=True)
    pipe.enable_model_cpu_offload()
    for n in range(3):
        s=int(seed)+n*1009; g=torch.Generator(device="cpu").manual_seed(s)
        with torch.inference_mode(): im=pipe(prompt=prompt,negative_prompt=negative_prompt,width=w,height=h,num_inference_steps=steps,guidance_scale=0.0,generator=g).images[0]
        q=_validate_image(im)
        if q["passed"]: break
    if not q["passed"]: raise RuntimeError(f"Hero image failed quality check: {q}")
    p=f"/tmp/{uuid.uuid4().hex}.png"; im.save(p)
    key=_upload_image(p,uuid.uuid4().hex)
    return {"type":"image","object_key":key,"seed":s,"model":model,"quality":q}

@app.function(image=image,gpu="L40S",timeout=3600,secrets=[secret])
def animate_promo(image_object_key:str,audio_key:str,clip_start:float,clip_duration:float,motion_prompt:str,
                  platform:str,quality_mode:str="fast",seed:int=42,key_lyric:str=""):
    import os,uuid,torch
    from PIL import Image
    from diffusers import CogVideoXImageToVideoPipeline
    from diffusers.utils import export_to_video,load_image
    
    model=os.environ.get("I2V_MODEL","zai-org/CogVideoX-5b-I2V")
    work=f"/tmp/v4_{uuid.uuid4().hex}";os.makedirs(work)
    ip=os.path.join(work,"hero.png");_download_object(image_object_key,ip)
    src=Image.open(ip).convert("RGB")
    if "9:16" in platform: w,h=480,720
    elif "1:1" in platform:w,h=720,720
    else:w,h=720,480
    src=src.resize((w,h),Image.Resampling.LANCZOS);src.save(ip)
    pipe=CogVideoXImageToVideoPipeline.from_pretrained(model,torch_dtype=torch.bfloat16,low_cpu_mem_usage=True)
    pipe.vae.enable_tiling();pipe.vae.enable_slicing();pipe.enable_model_cpu_offload()
    # Generate ~6s of good motion, then create a seamless-feeling 10–15s ad by forward/reverse looping.
    steps={"fast":20,"better":30,"best":40}.get(quality_mode,20)
    g=torch.Generator(device="cpu").manual_seed(int(seed))
    with torch.inference_mode():
        out=pipe(image=load_image(ip),prompt=motion_prompt,num_videos_per_prompt=1,num_inference_steps=steps,
                 num_frames=49,guidance_scale=6.0,use_dynamic_cfg=True,generator=g)
    raw=os.path.join(work,"raw.mp4");export_to_video(out.frames[0],raw,fps=8)
    loop=os.path.join(work,"loop.mp4")
    # Ping-pong avoids a hard reset at the loop boundary.
    _run(["ffmpeg","-y","-loglevel","error","-i",raw,"-filter_complex",
          f"[0:v]scale={w}:{h},split[a][b];[b]reverse[r];[a][r]concat=n=2:v=1:a=0,loop=loop=-1:size=96:start=0,trim=duration={float(clip_duration):.3f},setpts=PTS-STARTPTS[v]",
          "-map","[v]","-an","-r","8","-c:v","libx264","-pix_fmt","yuv420p",loop])
    ap=os.path.join(work,"audio"+(os.path.splitext(audio_key)[1] or ".mp3"));_download_object(audio_key,ap)
    final=os.path.join(work,"promo.mp4")
    _run(["ffmpeg","-y","-loglevel","error","-i",loop,"-ss",f"{float(clip_start):.3f}","-t",f"{float(clip_duration):.3f}","-i",ap,
          "-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-b:a","192k","-shortest","-movflags","+faststart",final])
    q=_quality(final)
    if not q["passed"]:raise RuntimeError(f"Animation failed quality gate: {q}")
    key=_upload_video(final,uuid.uuid4().hex)
    return {"type":"video","object_key":key,"model":model,"quality":q,"clip_start":clip_start,"clip_duration":clip_duration}
