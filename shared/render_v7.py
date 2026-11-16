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
        # Reference-style neon highway: purple star field, orange perspective rails,
        # dashed central lane and two stylized low-poly cars.
        import random
        rng=random.Random(117)
        for _ in range(145):
            x=rng.randrange(W); y=rng.randrange(H)
            r=1 if rng.random()<.93 else 2
            d.ellipse((x-r,y-r,x+r,y+r),fill=(216,195,230,rng.randrange(75,180)))
        horizon=310
        d.polygon([(W//2-18,horizon),(W//2+18,horizon),(W+95,H),(-95,H)],fill=(8,9,24,255))
        d.line([(W//2-18,horizon),(-95,H)],fill=(247,103,66,240),width=3)
        d.line([(W//2+18,horizon),(W+95,H)],fill=(247,103,66,240),width=3)
        # Lane markers advance towards the viewer as the music plays.
        for j in range(10):
            depth=((j/10+t*.20)%1)**1.65
            y=int(horizon+depth*(H-horizon))
            width=max(1,int(1+depth*5));height=int(5+depth*42)
            d.line([(W//2,y),(W//2,y+height)],fill=(210,201,218,210),width=width)
        def car(cx,cy,scale,body,window):
            cw=int(115*scale);ch=int(62*scale)
            pts=[(cx-cw//2,cy),(cx-cw//3,cy-ch//2),(cx+cw//3,cy-ch//2),(cx+cw//2,cy),
                 (cx+cw//2-10*scale,cy+ch//3),(cx-cw//2+10*scale,cy+ch//3)]
            d.polygon(pts,fill=body)
            d.polygon([(cx-cw*.26,cy-ch*.32),(cx-cw*.18,cy-ch*.46),(cx+cw*.18,cy-ch*.46),(cx+cw*.28,cy-ch*.32)],fill=window)
            d.line([(cx-cw*.38,cy+ch*.08),(cx-cw*.16,cy+ch*.08)],fill=(255,183,107,220),width=max(2,int(4*scale)))
            d.line([(cx+cw*.16,cy+ch*.08),(cx+cw*.38,cy+ch*.08)],fill=(255,183,107,220),width=max(2,int(4*scale)))
        car(int(W*.29),int(H*.69),1.05,(181,49,66,255),(30,15,34,255))
        car(int(W*.75),int(H*.82),1.1,(55,137,176,255),(24,41,63,255))
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
    d=ImageDraw.Draw(im,'RGBA')
    nearest=next((i for i,w in enumerate(words) if float(w['start'])<=t<float(w['end'])),None)
    if nearest is None:nearest=min(range(len(words)),key=lambda i:abs(float(words[i]['start'])-t))
    # Keep a coherent phrase on screen, with the sung word outlined in orange.
    lo=max(0,(nearest//11)*11);hi=min(len(words),lo+11)
    visible=words[lo:hi]
    font=_font(43)
    lines=[];line=[];width=0
    for idx,w in enumerate(visible,lo):
        token=str(w['word']).strip()
        token_width=d.textbbox((0,0),token+' ',font=font)[2]
        if line and width+token_width>W-45:
            lines.append(line);line=[];width=0
        line.append((idx,token));width+=token_width
    if line:lines.append(line)
    if len(lines)>5:
        font=_font(36)
        lines=[];line=[];width=0
        for idx,w in enumerate(visible,lo):
            token=str(w['word']).strip();tw=d.textbbox((0,0),token+' ',font=font)[2]
            if line and width+tw>W-45:lines.append(line);line=[];width=0
            line.append((idx,token));width+=tw
        if line:lines.append(line)
    line_height=int(font.size*1.08) if hasattr(font,'size') else 46
    y=int(H*.37-len(lines)*line_height/2)
    for line in lines:
        full=' '.join(token for _,token in line)
        line_width=d.textbbox((0,0),full,font=font)[2]
        x=(W-line_width)//2
        for idx,token in line:
            bbox=d.textbbox((0,0),token,font=font)
            tw=bbox[2]
            if idx==nearest:
                # Preserve the entire actual sung duration (including long
                # held vowels). The underline fills across that duration.
                w=words[idx]
                span=max(0.001,float(w['end'])-float(w['start']))
                progress=max(0.0,min(1.0,(t-float(w['start']))/span))
                d.rounded_rectangle((x-5,y-2,x+tw+5,y+line_height-3),radius=5,outline=(255,105,65,255),width=2)
                d.rounded_rectangle((x,y+line_height-7,x+max(2,int(tw*progress)),y+line_height-3),radius=2,fill=(255,122,68,255))
                color=(255,111,72,255)
            else:color=(238,236,242,255)
            d.text((x,y),token,font=font,fill=color,stroke_width=1,stroke_fill=(8,6,18,230))
            x+=d.textbbox((0,0),token+' ',font=font)[2]
        y+=line_height

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
