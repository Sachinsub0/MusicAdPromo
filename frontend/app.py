"""Simple MusicAdPromo v4 UI."""
from __future__ import annotations
import json,os,time,requests
from dotenv import load_dotenv
import streamlit as st
load_dotenv();BACKEND=os.environ.get("BACKEND_URL","http://localhost:8000")
st.set_page_config(page_title="MusicAdPromo v4",page_icon="🎵",layout="wide")
st.title("🎵 MusicAdPromo v4")
st.caption("Understand the song → create one visual → animate it.")
with st.sidebar:
    duration=st.slider("Promo length",10,15,12)
    platform=st.selectbox("Format",["TikTok / Reels (9:16)","Square (1:1)","Landscape (16:9)"])
    image_quality=st.selectbox("Image quality",["fast","better","best"],index=1)
    video_quality=st.selectbox("Animation quality",["fast","better","best"],index=0)
    seed=st.number_input("Seed",0,999999,42)
audio=st.file_uploader("Song",type=["mp3","wav","m4a"])
c1,c2=st.columns(2)
with c1:
    title=st.text_input("Track title");genre=st.selectbox("Genre",["Hip Hop","R&B","Pop","Electronic","Rock","Afrobeats","House","Other"])
with c2:
    lyrics=st.text_area("Lyrics",height=170,placeholder="Paste the lyrics. The app uses them to understand theme, emotion and imagery.")
    direction=st.text_input("Optional visual idea",placeholder="e.g. alone in a car at night — or leave blank")
for k,v in {"analysis":None,"hero":None,"video":None,"image_prompt":"","motion_prompt":""}.items():
    if k not in st.session_state:st.session_state[k]=v
def poll(job,label):
    box=st.empty();start=time.time()
    while True:
        box.write(f"⏳ {label} · {int(time.time()-start)}s")
        r=requests.get(f"{BACKEND}/status/{job}",timeout=30);d=r.json()
        if d.get("status")=="done":box.write(f"✅ {label} complete");return d
        if d.get("status")=="failed":st.error(d.get("error"));return None
        time.sleep(2.5)
def analyze(selected=None):
    audio.seek(0)
    data={"lyrics":lyrics,"genre":genre,"clip_duration":duration,"visual_direction":direction}
    if selected is not None:data["selected_start"]=selected
    r=requests.post(f"{BACKEND}/analyze",files={"audio":(audio.name,audio.read(),audio.type)},data=data,timeout=180);audio.seek(0)
    if not r.ok:st.error(r.text);return
    st.session_state.analysis=r.json();st.session_state.hero=None;st.session_state.video=None
    st.session_state.image_prompt=r.json()["visual"]["image_prompt"];st.session_state.motion_prompt=r.json()["visual"]["motion_prompt"]
if st.button("🧠 Analyze song",type="primary",use_container_width=True):
    if not audio:st.error("Upload a song first.")
    else:analyze()
a=st.session_state.analysis
if not a:
    st.info("Upload the song and lyrics, then analyze. No GPU is used during analysis.");st.stop()
st.subheader("Song understanding")
m=a["mood"];l=a["lyrics"]
x,y,z=st.columns(3)
x.metric("Selected hook",f"{a['clip_start']:.1f}–{a['clip_start']+a['clip_duration']:.1f}s")
y.metric("Tempo",f"{m['tempo_bpm']} BPM");z.metric("Energy",m["energy"])
st.write("**Mood:** "+ " · ".join(m["mood_labels"]))
st.write(f"**Lyric theme:** {l['theme']}")
st.write(f"**Interpretation:** {l['summary']}")
if l.get("key_lyric"):st.write(f"**Suggested lyric:** “{l['key_lyric']}”")
with st.expander("Other recommended promo moments"):
    for i,c in enumerate(a["candidates"]):
        if st.button(f"Use {c['start']:.1f}s · score {c['score']:.2f}",key=f"c{i}"):analyze(c["start"]);st.rerun()
st.subheader("One visual concept")
st.info(a["visual"]["concept"])
st.session_state.image_prompt=st.text_area("Image prompt",st.session_state.image_prompt,height=180)
if st.button("🖼️ Generate / regenerate hero image",type="primary",use_container_width=True):
    r=requests.post(f"{BACKEND}/generate-image",data={"analysis_json":json.dumps(a),"platform":platform,"seed":int(seed),"quality_mode":image_quality,"custom_prompt":st.session_state.image_prompt},timeout=60)
    if r.ok:
        d=poll(r.json()["job_id"],"Generating hero image")
        if d:st.session_state.hero=d;st.rerun()
    else:st.error(r.text)
hero=st.session_state.hero
if hero:
    st.image(hero["url"])
    st.caption("This is the only visual the video model will animate. Regenerate it until you actually like it.")
    st.subheader("Animation")
    st.session_state.motion_prompt=st.text_area("Motion prompt",st.session_state.motion_prompt,height=150)
    if st.button("🎬 Animate this image",type="primary",use_container_width=True):
        if not audio:st.error("Re-upload the song.")
        else:
            audio.seek(0)
            r=requests.post(f"{BACKEND}/generate-video",files={"audio":(audio.name,audio.read(),audio.type)},data={
                "analysis_json":json.dumps(a),"image_object_key":hero["object_key"],"platform":platform,
                "quality_mode":video_quality,"seed":int(seed),"custom_motion_prompt":st.session_state.motion_prompt},timeout=180)
            audio.seek(0)
            if r.ok:
                d=poll(r.json()["job_id"],"Animating visual + attaching song")
                if d:st.session_state.video=d;st.rerun()
            else:st.error(r.text)
if st.session_state.video:
    st.success("Final promo")
    st.video(st.session_state.video["url"])
    st.link_button("Open final MP4",st.session_state.video["url"],use_container_width=True)
