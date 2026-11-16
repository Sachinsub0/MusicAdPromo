"""Lightweight self-contained v7 scene renderer; does not claim to reproduce legacy assets."""
import io, math, os, subprocess, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from shared.audio import wav_bytes

TEMPLATES = {
    'neon_racecars': 'Neon Racecars',
    'skyline': 'Skyline',
    'nightclub': 'Nightclub',
    'sunset_coast': 'Sunset Coast',
}
W,H,FPS=540,960,12
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

def _font(size):
    try:return ImageFont.truetype(FONT,size)
    except OSError:return ImageFont.load_default()

def _background(template,t):
    palette={
        'neon_racecars':((9,10,33),(69,13,71)),
        'skyline':((5,23,58),(22,80,116)),
        'nightclub':((25,5,51),(80,11,84)),
        'sunset_coast':((246,108,87),(59,33,100)),
    }
    top,bottom=palette[template]
    arr=np.zeros((H,W,3),dtype=np.uint8)
    for i in range(3):arr[:,:,i]=np.linspace(top[i],bottom[i],H,dtype=np.uint8)[:,None]
    im=Image.fromarray(arr,'RGB');d=ImageDraw.Draw(im,'RGBA')
    if template=='sunset_coast':
        cy=420+int(8*math.sin(t*.4));d.ellipse((155,cy-100,385,cy+130),fill=(255,208,118,225))
        d.polygon([(0,600),(W,600),(W,H),(0,H)],fill=(25,56,106,210))
        for j in range(10):
            y=630+j*28;d.line((0,y,W,y+int(7*math.sin(t+j))),fill=(251,182,134,55),width=3)
    elif template=='skyline':
        for i in range(18):
            x=i*33;hh=130+(i*73)%290;d.rectangle((x,H-hh,x+29,H),fill=(5,14,39,245))
            for y in range(H-hh+12,H-8,23):
                if (i+y//23)%3:d.rectangle((x+8,y,x+12,y+7),fill=(71,219,244,150))
    elif template=='nightclub':
        for i in range(9):
            x=int(W/2+math.sin(t*.8+i*1.7)*W*.7)
            d.polygon([(W//2,0),(x-28,H),(x+28,H)],fill=(220 if i%2 else 41,60,250,22))
        for i in range(6):d.ellipse((i*103-10,680,i*103+65,755),outline=(255,69,223,90),width=4)
    else:
        road=[(W//2-55,570),(W//2+55,570),(W+110,H),(-110,H)]
        d.polygon(road,fill=(11,13,35,245))
        for i in range(12):
            y=int((i*117+t*120)%H)
            d.line((W//2,y,W//2,y+34),fill=(255,65,210,180),width=4)
        d.polygon([(165,670),(375,670),(430,780),(110,780)],fill=(26,15,63,255))
        d.rectangle((125,748,184,766),fill=(255,34,126,255));d.rectangle((355,748,414,766),fill=(255,34,126,255))
    return im

def _wrap(draw,text,font,max_width):
    lines=[];current=''
    for word in text.split():
        candidate=(current+' '+word).strip()
        if draw.textbbox((0,0),candidate,font=font)[2]>max_width and current:
            lines.append(current);current=word
        else:current=candidate
    if current:lines.append(current)
    return lines[-5:]

def _lyrics_frame(im,words,t):
    if not words:return
    active=[w for w in words if float(w['start'])<=t<=float(w['end'])]
    nearest=next((i for i,w in enumerate(words) if float(w['start'])<=t<float(w['end'])),None)
    if nearest is None:
        nearest=min(range(len(words)),key=lambda i:abs(float(words[i]['start'])-t))
    lo=max(0,nearest-5);hi=min(len(words),nearest+6)
    text=' '.join(str(w['word']) for w in words[lo:hi]);d=ImageDraw.Draw(im,'RGBA')
    font=_font(36);lines=_wrap(d,text,font,W-72)
    if not lines:return
    y=H//2-(len(lines)*49)//2
    d.rounded_rectangle((20,y-26,W-20,y+len(lines)*49+18),radius=20,fill=(0,0,0,135))
    for line in lines:
        bbox=d.textbbox((0,0),line,font=font);x=(W-(bbox[2]-bbox[0]))//2
        d.text((x,y),line,font=font,fill=(255,255,255,255),stroke_width=2,stroke_fill=(0,0,0,220));y+=49
    if active:d.rounded_rectangle((W//2-38,y+2,W//2+38,y+7),radius=3,fill=(255,216,99,255))

def render_mp4(y,sr,template,words=None):
    if template not in TEMPLATES:raise ValueError('Unknown template')
    if not 10<=len(y)/sr<=25.1:raise ValueError('Clip duration must be 10–25 seconds')
    with tempfile.TemporaryDirectory() as tmp:
        wav=os.path.join(tmp,'clip.wav');out=os.path.join(tmp,'promo.mp4')
        with open(wav,'wb') as f:f.write(wav_bytes(y,sr))
        cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','pipe:0','-i',wav,'-c:v','libx264','-preset','ultrafast','-crf','28','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k','-shortest','-movflags','+faststart',out]
        proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
        try:
            for i in range(math.ceil(len(y)/sr*FPS)):
                t=i/FPS;im=_background(template,t);_lyrics_frame(im,words or [],t)
                proc.stdin.write(im.tobytes())
            proc.stdin.close();error=proc.stderr.read().decode(errors='replace');rc=proc.wait()
            if rc:raise RuntimeError('FFmpeg rendering failed: '+error[-1200:])
            with open(out,'rb') as f:return f.read()
        except Exception:
            proc.kill();proc.wait();raise
