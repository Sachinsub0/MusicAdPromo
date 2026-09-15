from __future__ import annotations
import os,math,tempfile,subprocess
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
import imageio_ffmpeg
W,H,FPS=540,960,30
def _font(n):
 for p in ["/System/Library/Fonts/Supplemental/Arial Bold.ttf","/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]:
  if os.path.exists(p):
   try:return ImageFont.truetype(p,n)
   except:pass
 return ImageFont.load_default()
def _pulse(t,events,width=.12):
 return max([max(0,1-abs(t-e)/width) for e in events]+[0])
def render(plan,audio,out,background=None):
 tmp=tempfile.mkdtemp(prefix="v6_");fd=os.path.join(tmp,"f");os.makedirs(fd);duration=float(plan["duration"]);words=plan["words"];beats=plan["timeline"]["beats"];ons=plan["timeline"]["onsets"]
 if background and os.path.exists(background):
  bg=Image.open(background).convert("RGB");ratio=max(W/bg.width,H/bg.height);bg=bg.resize((int(bg.width*ratio),int(bg.height*ratio)),Image.Resampling.LANCZOS);left=(bg.width-W)//2;top=(bg.height-H)//2;bg=bg.crop((left,top,left+W,top+H))
 else:
  bg=Image.new("RGB",(W,H),(10,10,18))
 # phrases use actual timing, not arbitrary redistribution
 groups=[];g=[]
 for w in words:
  if g and (len(g)>=5 or w["start"]-g[-1]["end"]>.55):groups.append(g);g=[]
  g.append(w)
 if g:groups.append(g)
 for fi in range(round(duration*FPS)):
  t=fi/FPS;beatp=_pulse(t,beats,.09);onp=_pulse(t,ons,.07)
  # restrained animated-image effect: slow Ken Burns + beat micro-pulse. Works with generated OR uploaded still.
  scale=1.035+.018*(t/duration)+.008*beatp
  nw,nh=int(W*scale),int(H*scale);im=bg.resize((nw,nh),Image.Resampling.LANCZOS);x=(nw-W)//2+int(math.sin(t*.35)*4);y=(nh-H)//2;im=im.crop((x,y,x+W,y+H))
  overlay=Image.new("RGBA",(W,H),(0,0,0,75));im=Image.alpha_composite(im.convert("RGBA"),overlay).convert("RGB");d=ImageDraw.Draw(im)
  active=next((g for g in groups if g[0]["start"]-.12<=t<=g[-1]["end"]+.25),None)
  if active:
   # display phrase, highlight exactly active aligned word
   sizes=[];total=0
   for w in active:
    active_word=w["start"]<=t<=w["end"];sz=64 if active_word else 52;f=_font(sz);bb=d.textbbox((0,0),w["word"],font=f);ww=bb[2]-bb[0];sizes.append((f,ww,sz,active_word));total+=ww+14
   x0=max(20,(W-total+14)/2);yy=H*.55
   for w,(f,ww,sz,isactive) in zip(active,sizes):
    alpha=255 if t>=w["start"]-.08 else 70;dx=dy=0;sc=1
    local=(t-w["start"])/max(.04,w["end"]-w["start"])
    if isactive:
     # Beat/onset affects HOW the active word moves, never WHEN it appears.
     sc+=.10*beatp+.08*onp
     if w["effect"]=="shake":dx=math.sin(t*60)*7
     elif w["effect"]=="fall":dy=-35*(1-max(0,min(1,local)))
     elif w["effect"]=="rise":dy=35*(1-max(0,min(1,local)))
     elif w["effect"]=="bounce":dy=-abs(math.sin(local*math.pi*2))*24
     elif w["effect"]=="stretch":sc+=.12*max(0,min(1,local))
     elif w["effect"]=="pulse":sc+=.08*math.sin(max(0,local)*math.pi)
    ff=_font(max(16,int(sz*sc)));bb=d.textbbox((0,0),w["word"],font=ff);tw=bb[2]-bb[0]
    fill=(255,232,180) if isactive else (245,245,245)
    d.text((x0-(tw-ww)/2+dx,yy+dy),w["word"],font=ff,fill=fill,stroke_width=2,stroke_fill=(0,0,0))
    x0+=ww+14
  im.save(os.path.join(fd,f"{fi:05d}.jpg"),quality=92)
 ff=imageio_ffmpeg.get_ffmpeg_exe();silent=os.path.join(tmp,"silent.mp4")
 subprocess.run([ff,"-y","-loglevel","error","-framerate",str(FPS),"-i",os.path.join(fd,"%05d.jpg"),"-c:v","libx264","-pix_fmt","yuv420p",silent],check=True)
 subprocess.run([ff,"-y","-loglevel","error","-i",silent,"-ss",str(plan["clip_start"]),"-t",str(duration),"-i",audio,"-map","0:v","-map","1:a:0","-c:v","copy","-c:a","aac","-b:a","192k","-shortest","-movflags","+faststart",out],check=True)
 return out
