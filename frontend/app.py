import os,sys,io,json,requests,streamlit as st
import pandas as pd
sys.path.insert(0,os.path.dirname(os.path.dirname(__file__)))
from shared.alignment_v7 import approximate_alignment, preserve_alignment_on_edit

st.set_page_config(page_title='MusicAdPromo v7',page_icon='🎵',layout='wide')
st.title('🎵 MusicAdPromo v7')
st.caption('Choose the hook. Correct the lyrics. Create your promo.')
BASE=os.environ.get('BACKEND_URL','http://127.0.0.1:8000').rstrip('/')
audio=st.file_uploader('Upload your song (up to 200 MB)',type=['mp3','wav','m4a'])
duration=st.slider('Promo duration (seconds)',10,25,15)
if not audio:st.stop()
if audio.size>200*1024*1024:
    st.error(f'Song is {audio.size/1024/1024:.1f} MB; maximum is 200 MB.')
    st.stop()
raw=audio.getvalue();name=audio.name
key=(name,len(raw),duration)
if st.session_state.get('song_key')!=key:
    st.session_state.song_key=key
    st.session_state.pop('hooks',None)
    st.session_state.pop('timings',None)
    st.session_state.pop('selection',None)
    st.session_state.pop('rendered_mp4',None)
    st.session_state.pop('lyric_text',None)
    st.session_state.pop('timings_lyrics',None)

def send(path,fields):
    try:
        r=requests.post(BASE+path,files={'audio':(name,raw,'application/octet-stream')},data=fields,timeout=180)
        if not r.ok:
            try:
                detail=r.json().get('detail',r.text)
            except ValueError:
                detail=r.text[:800]
            st.error(f'Backend rejected the request (HTTP {r.status_code}): {detail}')
            return None
        return r
    except requests.RequestException as exc:
        st.error(f'Backend connection error: {exc}');return None

if st.button('Find five recommended sections'):
    with st.spinner('Analyzing song energy and onsets...'):
        r=send('/v7/hooks',{'duration':duration})
        if r is not None:
            st.session_state.hooks=r.json()
            st.session_state.selection=None

hooks=st.session_state.get('hooks')
if hooks:
    song_duration=hooks['duration']
    st.caption('Suggestions are ranked by energy and onset activity, not lyrical catchiness.')
    options=[f"#{i+1} · {h['start']:.1f}s–{h['end']:.1f}s" for i,h in enumerate(hooks['hooks'])]
    choice=st.radio('Select a recommended hook or your own section',options+['Custom section'])
    if choice=='Custom section':
        start=st.slider('Start time (seconds)',0.0,max(0.0,float(song_duration-duration)),0.0,step=0.1)
    else:start=float(hooks['hooks'][options.index(choice)]['start'])
    st.info(f'Selected: {start:.1f}s–{start+duration:.1f}s')
    if st.button('Preview selected audio'):
        r=send('/v7/preview',{'start':start,'duration':duration})
        if r is not None:st.audio(r.content,format='audio/wav')
    st.subheader('Transcribed lyrics — editable')
    st.caption('Transcribe first, then fix any missed or incorrect words directly in the box. You can also paste your own lyrics.')
    language=st.text_input('Language code (optional, e.g. es, hi, en)',value='')
    if st.button('Transcribe selected clip with word timestamps'):
        with st.spinner('Running Whisper...'):
            r=send('/v7/align',{'start':start,'duration':duration,'lyrics':'','language':language})
            if r is not None:
                result=r.json()
                words=result.get('words',[])
                st.session_state.timings=words
                transcribed=' '.join(w['word'] for w in words)
                st.session_state.lyric_text=transcribed
                st.session_state.timings_lyrics=transcribed
                st.session_state.pop('rendered_mp4',None)
                st.warning(result.get('warning','Review the transcription and timings.'))
                st.caption('Detected language: '+str(result.get('detected_language','unknown')))
                st.rerun()
    lyrics=st.text_area('Lyrics for selected section',key='lyric_text',height=180,
                        placeholder='Transcribed lyrics appear here. Edit them freely, or paste your own.',
                        help='You can edit any words, including non-English lyrics. Apply changes to refresh timing rows.')
    if st.button('Apply edited lyrics to timing rows',disabled=not lyrics.strip()):
        # Edits to words cannot be assumed to preserve exact timestamps. Generate
        # an explicitly approximate draft for manual correction, never silently
        # retain timings for words that no longer match the text box.
        existing=st.session_state.get('timings',[])
        new_tokens=lyrics.split()
        old_tokens=[w['word'] for w in existing]
        if new_tokens==old_tokens:
            st.info('Lyrics already match the timing rows.')
        else:
            st.session_state.timings=preserve_alignment_on_edit(existing,lyrics,duration)
            st.session_state.timings_lyrics=lyrics
            st.session_state.pop('rendered_mp4',None)
            st.warning('Text changes applied. Existing word timings were preserved where possible; newly inserted words have estimated timings. Review them before rendering.')
            st.rerun()
    if 'timings' in st.session_state:
        st.subheader('Review and edit word timing')
        df=pd.DataFrame(st.session_state.timings,columns=['word','start','end'])
        edited=st.data_editor(df,num_rows='dynamic',hide_index=True,key='editor')
        if lyrics.split()!=[str(w) for w in edited['word'].tolist()]:
            st.warning('The lyrics text box and timing rows differ. Click “Apply edited lyrics to timing rows” before rendering.')
        if st.button('Validate and export timing JSON'):
            try:
                rows=edited.to_dict('records')
                response=requests.post(BASE+'/v7/validate-timings',json={'duration':duration,'words':rows},timeout=30)
                response.raise_for_status()
                st.download_button('Download corrected timings',data=response.text,file_name='lyric_timings.json',mime='application/json')
            except Exception as e:st.error(f'Invalid timings: {e}')
    st.divider()
    st.subheader('Create your lyric promo')
    template_names={'neon_racecars':'Neon Racecars','skyline':'Skyline','nightclub':'Nightclub','sunset_coast':'Sunset Coast'}
    template=st.selectbox('Cinematic template',list(template_names),format_func=lambda x:template_names[x])
    if st.button('Generate MP4 video',type='primary'):
        words=[]
        if 'timings' in st.session_state:
            words=edited.to_dict('records')
            if lyrics.split()!=[str(w['word']) for w in words]:
                st.error('Apply your edited lyrics to timing rows before rendering, so the MP4 uses the correct text.')
                st.stop()
        with st.spinner('Rendering your MP4 clip (may take a minute)...'):
            r=send('/v7/render',{'start':start,'duration':duration,'template':template,'words_json':json.dumps(words)})
            if r is not None:
                st.session_state.rendered_mp4=r.content
                st.session_state.rendered_key=(name,len(raw),duration,start,template)
    if st.session_state.get('rendered_mp4') and st.session_state.get('rendered_key')==(name,len(raw),duration,start,template):
        st.video(st.session_state.rendered_mp4)
        st.download_button('Download MP4',data=st.session_state.rendered_mp4,file_name='MusicAdPromo-v7.mp4',mime='video/mp4')
else:st.caption('Click Find five recommended sections to begin.')
