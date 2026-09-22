import streamlit as st,requests,json,os,hashlib
B=os.environ.get("BACKEND_URL","http://127.0.0.1:8000")
st.set_page_config(page_title="MusicAdPromo v6.2",page_icon="🎵",layout="wide");st.title("🎵 MusicAdPromo v6.2");st.caption("Automatic vocal transcription + word-aligned lyrics + beat/onset reactions.")
audio=st.file_uploader("Song",type=["mp3","wav","m4a"])
lyrics=st.text_area("Lyrics correction (optional)",height=150,placeholder="Leave blank to detect lyrics automatically from the song.",help="If you already have the official lyrics, paste them here to improve spelling. WhisperX still determines the timing.")
duration=st.slider("Promo length",10,15,12)
if "plan" not in st.session_state:st.session_state.plan=None
def analyze(start=None,lyrics_override=None):
 audio.seek(0);data={"lyrics":lyrics if lyrics_override is None else lyrics_override,"duration":duration}
 if start is not None:data["selected_start"]=start
 with st.spinner("Separating vocals and transcribing the selected hook..."):
  r=requests.post(B+"/analyze",files={"audio":(audio.name,audio.read(),audio.type)},data=data,timeout=1800)
 audio.seek(0)
 if r.ok:st.session_state.plan=r.json()
 else:st.error(r.text)
if st.button("🧠 Analyze + align",type="primary",use_container_width=True):
 if audio:analyze()
 else:st.error("Upload a song.")
p=st.session_state.plan
if p:
 st.subheader("Master timeline");a,b,c=st.columns(3);a.metric("Hook",f"{p['clip_start']:.2f}–{p['clip_start']+p['duration']:.2f}s");b.metric("Tempo",f"{p['timeline']['tempo_bpm']} BPM");c.metric("Strong onsets",len(p["timeline"]["onsets"]))
 st.write("**Mood:** "+" · ".join(p["creative"]["mood"]))
 transcription=p.get("transcription",{})
 separation=transcription.get("vocal_separation","unknown")
 if separation=="separated":st.success("Vocals isolated successfully before transcription.")
 elif separation.startswith("fallback"):
  st.warning("Vocal separation was unavailable, so transcription used the original mix. You can still review and correct the result below.")
 with st.expander("Other hook candidates"):
  for i,x in enumerate(p["candidates"]):
   if st.button(f"{x['start']:.2f}–{x['end']:.2f} · {x['score']}",key=i):analyze(x["start"]);st.rerun()
 st.subheader("Detected lyrics")
 plan_key=hashlib.md5(f"{p['clip_start']}|{p.get('detected_lyrics','')}".encode()).hexdigest()[:10]
 reviewed=st.text_area("Review and correct",value=p.get("detected_lyrics",""),height=140,key="review_"+plan_key,help="Fix names, slang, or words the model misheard, then re-align.")
 if st.button("🔁 Re-align corrected lyrics",use_container_width=True):
  analyze(p["clip_start"],reviewed);st.rerun()
 st.subheader("Alignment check")
 st.caption("WhisperX determines when each word appears. Beats affect animation only; they never change lyric timing.")
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
