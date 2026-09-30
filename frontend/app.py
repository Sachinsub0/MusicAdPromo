import streamlit as st
import requests, json, os, hashlib, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.alignment import preview_corrections
from shared.director import decorate
from shared.templates import TEMPLATES, frame
B=os.environ.get('BACKEND_URL','http://127.0.0.1:8000').rstrip('/')
st.set_page_config(page_title='MusicAdPromo',page_icon='🎵',layout='wide')
st.title('🎵 MusicAdPromo')
st.caption('Your song. A cinematic template. Lyrics that move with your vocals.')
audio=st.file_uploader('Song',type=['mp3','wav','m4a'])
lyrics=st.text_area('Hook lyrics (optional)',help='Paste only the lyrics sung in the selected hook. Leave blank for automatic detection.')
duration=st.slider('Promo length',10,15,12)
source_key=hashlib.sha256(audio.getvalue()).hexdigest() if audio else None
if st.session_state.get('source_key') != source_key:
 st.session_state.update(source_key=source_key,plan=None,video=None)
def analyze(start=None,lyrics_override=None):
 data={'lyrics':lyrics if lyrics_override is None else lyrics_override,'duration':duration}
 if start is not None:data['selected_start']=start
 try:
  with st.spinner('Analyzing vocals and aligning lyrics…'):
   r=requests.post(B+'/analyze',files={'audio':(audio.name,audio.getvalue(),audio.type)},data=data,timeout=1800)
  if r.ok:
   st.session_state.plan=r.json();st.session_state.video=None
   st.session_state.revision=st.session_state.get('revision',0)+1
   return True
  st.error(r.text)
 except requests.RequestException as exc:st.error(f'Could not reach the backend: {exc}')
 return False
if st.button('Analyze song',type='primary',use_container_width=True):
 if audio:analyze()
 else:st.error('Upload a song first.')
p=st.session_state.get('plan')
if p:
 a,b,c=st.columns(3)
 a.metric('Hook',f"{p['clip_start']:.2f}–{p['clip_start']+p['duration']:.2f}s")
 b.metric('Tempo',f"{p['timeline']['tempo_bpm']} BPM")
 c.metric('Mood',' · '.join(p['creative']['mood']))
 transcription=p.get('transcription',{})
 if transcription.get('vocal_separation','').startswith('fallback'):st.warning('Vocal separation was unavailable; please review the transcription from the original mix.')
 with st.expander('Other hook candidates'):
  for i,x in enumerate(p['candidates']):
   if st.button(f"{x['start']:.2f}–{x['end']:.2f}s",key=f'hook_{i}'):
    if analyze(x['start']):st.rerun()
 st.subheader('Detected lyrics')
 reviewed=st.text_area('Review and correct',value=p['detected_lyrics'],key=f"review_{st.session_state.get('revision',0)}",height=140,help='Edits update the alignment words immediately. Re-align to measure corrected word timing against the vocals.')
 dirty=reviewed.split()!=p['detected_lyrics'].split()
 shown=decorate(preview_corrections(p['words'],reviewed,p['duration']),p['timeline']) if dirty else p['words']
 if dirty:st.info('Your edits are shown below. Re-align corrected lyrics before rendering; changed-word times are provisional.')
 if st.button('Re-align corrected lyrics',disabled=not reviewed.strip(),use_container_width=True):
  if analyze(p['clip_start'],reviewed):st.rerun()
 st.subheader('Alignment check')
 st.caption('The words below always match the lyric editor. Beats affect animation; vocal alignment controls word timing.')
 st.dataframe([{'word':w['word'],'start':round(w['start'],3),'end':round(w['end'],3),'confidence':round(w.get('score',0),2),'timing':'Estimated' if w.get('estimated') else 'Aligned','effect':w['effect']} for w in shown],hide_index=True,use_container_width=True)
 estimated=sum(w.get('estimated',False) for w in shown)
 if estimated:st.warning(f'{estimated} word(s) have estimated timing. Review them before rendering.')
 st.subheader('Visual template')
 choice=st.selectbox('Scene',['auto']+list(TEMPLATES),format_func=lambda x:'Automatic — match song mood' if x=='auto' else TEMPLATES[x]['name'])
 selected=p['template'] if choice=='auto' else choice
 st.caption(TEMPLATES[selected]['name']+' · '+TEMPLATES[selected]['description'])
 st.image(frame(selected,1.5),width=270)
 if duration!=p['duration']:st.info('Analyze again to apply the new promo length.')
 if st.button('Render lyric video',type='primary',use_container_width=True,disabled=dirty or not shown or duration!=p['duration']):
  try:
   render_plan={**p,'template':selected}
   with st.spinner('Rendering animated template and synced lyrics…'):
    r=requests.post(B+'/render',files={'audio':(audio.name,audio.getvalue(),audio.type)},data={'plan_json':json.dumps(render_plan)},timeout=1800)
   if r.ok:st.session_state.video=B+'/video/'+r.json()['video_id']
   else:st.error(r.text)
  except requests.RequestException as exc:st.error(f'Render request failed: {exc}')
if st.session_state.get('video'):st.video(st.session_state.video)
