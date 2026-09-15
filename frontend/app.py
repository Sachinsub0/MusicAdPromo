import streamlit as st,requests,json,os
B=os.environ.get("BACKEND_URL","http://127.0.0.1:8000")
st.set_page_config(page_title="MusicAdPromo v6",page_icon="🎵",layout="wide");st.title("🎵 MusicAdPromo v6");st.caption("Animated cover-art atmosphere + word-aligned lyrics + beat/onset reactions.")
audio=st.file_uploader("Song",type=["mp3","wav","m4a"]);lyrics=st.text_area("Full lyrics",height=180);duration=st.slider("Promo length",10,15,12)
if "plan" not in st.session_state:st.session_state.plan=None
def analyze(start=None):
 audio.seek(0);data={"lyrics":lyrics,"duration":duration}
 if start is not None:data["selected_start"]=start
 r=requests.post(B+"/analyze",files={"audio":(audio.name,audio.read(),audio.type)},data=data,timeout=1800);audio.seek(0)
 if r.ok:st.session_state.plan=r.json()
 else:st.error(r.text)
if st.button("🧠 Analyze + align",type="primary",use_container_width=True):
 if audio:analyze()
 else:st.error("Upload a song.")
p=st.session_state.plan
if p:
 st.subheader("Master timeline");a,b,c=st.columns(3);a.metric("Hook",f"{p['clip_start']:.2f}–{p['clip_start']+p['duration']:.2f}s");b.metric("Tempo",f"{p['timeline']['tempo_bpm']} BPM");c.metric("Strong onsets",len(p["timeline"]["onsets"]))
 st.write("**Mood:** "+" · ".join(p["creative"]["mood"]))
 with st.expander("Other hook candidates"):
  for i,x in enumerate(p["candidates"]):
   if st.button(f"{x['start']:.2f}–{x['end']:.2f} · {x['score']}",key=i):analyze(x["start"]);st.rerun()
 st.subheader("Alignment check")
 st.caption("These timestamps come from WhisperX forced alignment. Lyric appearance uses these timestamps directly; beats do not move the lyric timing.")
 st.dataframe([{"word":w["word"],"start":round(w["start"],3),"end":round(w["end"],3),"score":round(w.get("score",0),2),"effect":w["effect"]} for w in p["words"]],use_container_width=True,hide_index=True)
 st.subheader("Visual layer")
 st.code(p["image_prompt"],language=None)
 bg=st.file_uploader("Upload one hero/background image",type=["png","jpg","jpeg"],help="For v6 sync testing, this can be any still. The renderer adds restrained Ken Burns + beat micro-pulses. This keeps visual generation separate from timing reliability.")
 if bg:st.image(bg)
 if st.button("🎬 Render synced promo",type="primary",use_container_width=True):
  audio.seek(0);files={"audio":(audio.name,audio.read(),audio.type)}
  if bg:files["background"]=(bg.name,bg.getvalue(),bg.type)
  with st.spinner("Rendering 30fps master timeline..."):r=requests.post(B+"/render",files=files,data={"plan_json":json.dumps(p)},timeout=1800)
  audio.seek(0)
  if r.ok:st.session_state.video=B+"/video/"+r.json()["video_id"]
  else:st.error(r.text)
if st.session_state.get("video"):st.video(st.session_state.video)
