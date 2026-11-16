import re
from difflib import SequenceMatcher

def validate_words(words, duration):
    result=[]
    for item in words:
        word=str(item['word']).strip();start=float(item['start']);end=float(item['end'])
        if not word or not 0<=start<end<=duration+0.02: raise ValueError('Word timings must be inside selected clip')
        result.append({'word':word,'start':round(start,3),'end':round(end,3)})
    return sorted(result,key=lambda w:w['start'])

def approximate_alignment(lyrics,duration):
    # Fallback is explicitly NOT accurate alignment; user must review.
    words=re.findall(r'\S+',lyrics,flags=re.UNICODE)
    if not words:return []
    unit=duration/len(words)
    return [{'word':w,'start':round(i*unit,3),'end':round((i+1)*unit,3)} for i,w in enumerate(words)]

def align_clip(wav_path, lyrics, language=None):
    """Whisper word timestamps with corrected-text fallback; no false accuracy guarantees."""
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError('Install optional faster-whisper dependency for automatic alignment') from exc
    model=WhisperModel('small',device='cpu',compute_type='int8')
    segments, info=model.transcribe(wav_path,language=language or None,word_timestamps=True,vad_filter=False)
    words=[]
    for segment in segments:
        for w in segment.words or []:
            if w.start is not None and w.end is not None and w.end>w.start:
                words.append({'word':w.word.strip(),'start':round(w.start,3),'end':round(w.end,3)})
    # Whisper is transcription, not forced alignment of user-supplied lyrics.
    # Never pretend corrected lyrics were aligned when they weren't.
    return {'words':words,'detected_language':info.language,'provided_lyrics':lyrics,
            'warning':'Review each word. Supplied lyrics are not forced-aligned in this starter.'}


def preserve_alignment_on_edit(old_words, edited_lyrics, duration):
    """Keep timings of unchanged Whisper words; interpolate only changed spans.

    This is an editing convenience, NOT forced alignment. New words must be
    listened to and checked. Original elongated word intervals stay intact.
    """
    tokens=re.findall(r'\S+', edited_lyrics, flags=re.UNICODE)
    if not tokens:return []
    old=validate_words(old_words,duration) if old_words else []
    if not old:return approximate_alignment(edited_lyrics,duration)
    matcher=SequenceMatcher(None,[w['word'].casefold().strip('.,!?') for w in old],
                            [w.casefold().strip('.,!?') for w in tokens],autojunk=False)
    out=[None]*len(tokens)
    for tag,i1,i2,j1,j2 in matcher.get_opcodes():
        if tag=='equal':
            for i,j in zip(range(i1,i2),range(j1,j2)):
                out[j]={'word':tokens[j],'start':old[i]['start'],'end':old[i]['end']}
        elif tag=='replace' and (i2-i1)==(j2-j1):
            # Simple corrections (one misspelling for one word) retain duration.
            for i,j in zip(range(i1,i2),range(j1,j2)):
                out[j]={'word':tokens[j],'start':old[i]['start'],'end':old[i]['end']}
    # Insertions/deletions: estimate only the unmatched interval.
    i=0
    while i<len(out):
        if out[i] is not None:i+=1;continue
        j=i
        while j<len(out) and out[j] is None:j+=1
        left=out[i-1]['end'] if i else 0.0
        right=out[j]['start'] if j<len(out) else float(duration)
        if right<=left:
            # No gap between adjacent anchored words: preserve anchors and
            # give inserted words a small interval near the boundary.
            right=min(float(duration),left+0.05*(j-i))
            left=max(0.0,right-0.05*(j-i))
        step=(right-left)/(j-i)
        for k in range(i,j):
            out[k]={'word':tokens[k],'start':round(left+(k-i)*step,3),
                    'end':round(left+(k-i+1)*step,3)}
        i=j
    return out
