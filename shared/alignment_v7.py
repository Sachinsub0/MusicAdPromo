import re

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
