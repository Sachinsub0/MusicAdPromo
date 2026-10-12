"""Offline English lyric mood analysis: phrases, negation and mixed emotions.

This is an explainable heuristic, not a language model. Unclear lyrics use a neutral scene;
it must not turn a heartbreak hook into a racing scene just because it is loud.
"""
import re

LABELS = {
    'melancholic': ('melancholic', 'reflective', 'intimate'),
    'romantic': ('romantic', 'warm', 'intimate'),
    'dreamy': ('dreamy', 'hopeful', 'cinematic'),
    'confident': ('confident', 'energetic', 'kinetic'),
    'celebratory': ('celebratory', 'uplifting', 'energetic'),
    'dark': ('dark', 'tense', 'cinematic'),
}
CUES = {
    'melancholic': {'heartbroken', 'heartbreak', 'lonely', 'alone', 'pain', 'hurt', 'cry', 'crying', 'tears', 'lost', 'miss', 'missing', 'goodbye', 'sad', 'broken', 'regret', 'grief', 'questions'},
    'romantic': {'love', 'loving', 'kiss', 'kisses', 'beautiful', 'pretty', 'lover', 'darling', 'adore', 'cuddle'},
    'dreamy': {'dream', 'dreams', 'dreaming', 'stars', 'moon', 'floating', 'hope', 'healing', 'peace', 'breathe', 'ocean', 'sunrise'},
    'confident': {'win', 'winning', 'grind', 'hustle', 'boss', 'champion', 'unstoppable', 'money', 'guap', 'rich', 'diamonds', 'flex', 'race', 'racing', 'speed', 'fast', 'balling'},
    'celebratory': {'party', 'dance', 'dancing', 'celebrate', 'celebrating', 'cheers', 'happy', 'joy', 'laugh', 'laughing', 'fun'},
    'dark': {'rage', 'angry', 'anger', 'hate', 'revenge', 'demons', 'nightmare', 'fear', 'afraid', 'danger', 'blood', 'violent'},
}
PHRASES = {
    'melancholic': ['miss you', 'without you', 'you left', 'left me', 'broke my heart', 'broken heart', 'falling apart', 'love is gone', "don't love me", "doesn't love me", 'no love', 'love hurts', 'went wrong', 'questions in my head', 'focused on myself', 'felt lost'],
    'romantic': ['in love', 'hold me', 'hold you', 'by my side', 'you and me', 'with you', 'your touch'],
    'dreamy': ['be okay', 'be ok', 'better days', 'moving on', 'let it go', 'find my peace'],
    'confident': ['on top', 'my way', 'made it', 'never give up', "can't stop me", 'getting paid'],
    'celebratory': ['good time', 'good vibes', 'feel good', 'all night', 'hands up'],
    'dark': ['trust nobody', 'trust no one', 'in the shadows'],
}
NEGATORS = {'not', 'no', 'never', "don't", "dont", "can't", "cant", "won't", "wont", "isn't", "aint", "ain't"}

def analyze_lyrics(lyrics, timeline=None):
    text = (lyrics or '').lower().replace('’', "'")
    scores = dict.fromkeys(CUES, 0.0)
    evidence = {m: [] for m in CUES}
    # Punctuation/newlines end negation scope. Phrase spans prevent double counts.
    for clause in re.split(r'[\n.!?,;]+', text):
        tokens = re.findall(r"[a-z]+(?:'[a-z]+)?", clause)
        covered = set()
        hits = []
        for mood, phrases in PHRASES.items():
            for phrase in phrases:
                parts = phrase.split()
                for i in range(len(tokens) - len(parts) + 1):
                    if tokens[i:i+len(parts)] == parts:
                        hits.append((i, len(parts), mood, phrase))
        for i, size, mood, phrase in sorted(hits, key=lambda h: -h[1]):
            span = set(range(i, i+size))
            if span & covered or NEGATORS.intersection(tokens[max(0, i-2):i]):
                continue
            scores[mood] += 3
            evidence[mood].append(phrase)
            covered.update(span)
        for i, token in enumerate(tokens):
            if i in covered or NEGATORS.intersection(tokens[max(0, i-3):i]):
                continue
            for mood, cues in CUES.items():
                if token in cues:
                    scores[mood] += 1
                    evidence[mood].append(token)
    ranked = sorted(scores, key=lambda m: scores[m], reverse=True)
    primary = ranked[0]
    strong = scores[primary] >= 2
    if strong:
        # Sadness remains visible in bittersweet romantic lyrics.
        if scores['melancholic'] >= 2 and scores['melancholic'] >= scores[primary] * .7:
            primary = 'melancholic'
        secondary = [m for m in ranked if m != primary and scores[m] >= 2 and scores[m] >= scores[primary] * .5]
        moods = list(LABELS[primary])
        for m in secondary[:1]:
            moods.insert(1, m)
        matches = list(dict.fromkeys(evidence[primary]))[:4]
        reason = f"Lyrics suggest {primary}: " + ', '.join(matches) + '.'
        source = 'lyrics'
    else:
        primary = 'moody'
        moods = list(LABELS.get(primary, ('moody', 'cinematic', 'intimate')))
        reason = 'Lyric mood is unclear; using a neutral River skyline scene. Choose a scene manually if needed.'
        source = 'neutral_fallback'
    return {'mood': moods, 'primary_mood': primary, 'theme': ' / '.join(moods[:2]),
            'mood_source': source, 'mood_reason': reason,
            'lyric_scores': scores, 'lyric_evidence': evidence}
