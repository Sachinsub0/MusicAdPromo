"""Premade, deterministic animated scenes. No downloads or image uploads."""
import math, random
from functools import lru_cache
from PIL import Image, ImageDraw
TEMPLATES={
 'river_skyline':{'name':'River skyline','accent':(105,224,255),'description':'Blue-hour skyline, moving river reflections, cyan karaoke text.'},
 'racecars':{'name':'Neon racecars','accent':(255,114,74),'description':'Animated sports cars, neon highway, bold orange karaoke text.'},
 'dreamscape':{'name':'Moonlit dreamscape','accent':(225,166,255),'description':'Moonlit mountains, drifting stars, lilac karaoke text.'},
}
def recommend(creative,timeline,lyrics=''):
 words=set(lyrics.lower().split());moods=set(creative.get('mood',[]))
 if words & {'race','racing','car','cars','drive','speed','fast'} or 'energetic' in moods:return 'racecars'
 if moods & {'romantic','dreamy','longing'}:return 'dreamscape'
 return 'river_skyline'
@lru_cache(maxsize=12)
def _base(name,w,h):
 colors={'river_skyline':((12,16,44),(57,42,81)),'racecars':((12,8,32),(54,15,52)),'dreamscape':((13,12,43),(55,34,85))}
 top,bottom=colors[name];im=Image.new('RGB',(w,h));d=ImageDraw.Draw(im)
 for y in range(h):
  f=y/h;d.line((0,y,w,y),fill=tuple(int(a+(b-a)*f) for a,b in zip(top,bottom)))
 rng=random.Random(42)
 for _ in range(75):
  x,y=rng.randrange(w),rng.randrange(int(h*.5));d.ellipse((x,y,x+1,y+1),fill=(156,161,200))
 if name=='river_skyline':
  d.ellipse((w*.68,h*.13,w*.82,h*.13+w*.14),fill=(241,201,178))
  for x in range(-10,w,29):
   height=rng.randint(60,210);y=h*.48-height
   d.rectangle((x,y,x+25,h*.49),fill=(13,20,38))
   for yy in range(int(y+10),int(h*.47),14):
    for xx in range(x+5,x+23,8):
     if rng.random()>.35:d.rectangle((xx,yy,xx+2,yy+4),fill=(111,175,204))
  d.rectangle((0,h*.49,w,h),fill=(10,22,38))
 elif name=='dreamscape':
  d.ellipse((w*.64,h*.16,w*.84,h*.16+w*.2),fill=(225,212,249))
  for level,color in [(0,(38,35,68)),(1,(25,28,51)),(2,(18,23,39))]:
   y=h*(.43+level*.12);pts=[(0,h),(0,y)]
   pts += [(x,y-rng.randint(0,90)) for x in range(0,w+80,80)];pts +=[(w,h)]
   d.polygon(pts,fill=color)
 return im

def frame(name,t,beat=0,w=540,h=960):
 if name not in TEMPLATES:raise ValueError('Unknown visual template')
 im=_base(name,w,h).copy();d=ImageDraw.Draw(im);accent=TEMPLATES[name]['accent']
 if name=='river_skyline':
  for i in range(48):
   y=h*.51+i*h*.010;x=(i*47+math.sin(t*.8+i)*20)%w
   length=12+i*.8;d.line((x,y,x+length,y),fill=(28+i%4*12,67+i%5*9,89+i%6*9),width=2)
  d.line((0,h*.49,w,h*.49),fill=accent,width=2)
 elif name=='racecars':
  horizon=h*.41;d.polygon([(w*.4,horizon),(w*.6,horizon),(w,h),(0,h)],fill=(15,16,27))
  for side in [-1,1]:d.line((w/2+side*30,horizon,w/2+side*w*.47,h),fill=accent,width=3)
  for i in range(12):
   f=((i/12+t*.65)%1)**2;y=horizon+(h-horizon)*f
   d.line((w/2,y,w/2,y+8+f*26),fill=(204,186,207),width=max(1,int(2+f*5)))
  for cx,cy,color,phase in [(w*.28,h*.78,(229,66,70),0),(w*.74,h*.88,(75,168,220),2)]:
   cx+=math.sin(t*1.1+phase)*10;cy+=math.sin(t*1.7+phase)*8
   d.ellipse((cx-61,cy+24,cx+61,cy+46),fill=(6,7,14))
   d.polygon([(cx-49,cy+35),(cx-57,cy),(cx-32,cy-35),(cx+31,cy-35),(cx+56,cy),(cx+48,cy+35)],fill=color)
   d.polygon([(cx-26,cy-28),(cx+25,cy-28),(cx+39,cy-5),(cx-39,cy-5)],fill=(20,30,47))
   d.line((cx-45,cy+13,cx-23,cy+13),fill=(255,230,183),width=5)
   d.line((cx+23,cy+13,cx+45,cy+13),fill=(255,230,183),width=5)
   d.line((cx-44,cy-40,cx+44,cy-40),fill=(17,18,29),width=5)
 else:
  for i in range(14):
   x=(i*71+math.sin(t*.3+i)*16)%w;y=(i*59-t*9)%h
   d.ellipse((x,y,x+3+beat,y+3+beat),fill=accent)
 return im
