from __future__ import annotations
import re,math
MOTION={"fall":"fall","falling":"fall","rise":"rise","rising":"rise","shake":"shake","shaking":"shake","bounce":"bounce","spin":"spin","spinning":"spin","fly":"rise","flying":"rise","drive":"slide","running":"slide","run":"slide"}
EMO={"love","pretty","beautiful","heart","miss","lonely","alone","pain","hurt","dream","baby","girl","boy"}
def understand(lyrics,timeline):
 w=re.findall(r"[a-z']+",(lyrics or "").lower());rom=sum(x in {"love","pretty","baby","girl","boy","heart","kiss","miss","you"} for x in w);dark=sum(x in {"night","dark","alone","lonely","pain","hurt","cry","cold"} for x in w)
 if rom>=3 and dark>=1:mood=["romantic","longing","dreamy"]
 elif dark>=3:mood=["dark","melancholic","intimate"]
 elif timeline["energy"]>.7:mood=["energetic","confident","kinetic"]
 else:mood=["moody","cinematic","intimate"]
 return {"mood":mood,"theme":" / ".join(mood[:2])}
def decorate(words,timeline):
 beats=timeline["beats"];ons=timeline["onsets"];out=[]
 for w in words:
  x=w["word"].lower().strip(".,!?");dur=max(.03,w["end"]-w["start"]);effect="fade";kind="plain";imp=.2
  if x in MOTION:effect=MOTION[x];kind="semantic";imp=.95
  elif x in EMO:effect="pulse";kind="semantic";imp=.75
  elif dur>.75:effect="stretch";kind="vocal";imp=.8
  nearest=min(beats,key=lambda b:abs(b-w["start"])) if beats else None
  onset=min(ons,key=lambda b:abs(b-w["start"])) if ons else None
  out.append({**w,"kind":kind,"effect":effect,"importance":imp,"nearest_beat":nearest,"near_strong_onset":onset if onset is not None and abs(onset-w["start"])<.12 else None})
 # Limit semantic spectacle.
 special=sorted([w for w in out if w["kind"]!="plain"],key=lambda z:z["importance"],reverse=True)
 keep={id(x) for x in special[:max(2,math.ceil(len(out)*.3))]}
 for x in out:
  if x["kind"]!="plain" and id(x) not in keep:x["kind"]="plain";x["effect"]="fade"
 return out
def image_prompt(creative):
 mood=", ".join(creative["mood"])
 return f"Vertical 9:16 premium animated-cover-art background for a music lyric promo. Mood: {mood}. One simple cinematic environment, strong depth, practical lights, tasteful color contrast, atmospheric, high-end music editorial aesthetic. Keep the center and lower-middle visually uncluttered for large readable lyrics. No text, no logos, no typography, no collage, no extra UI."
