"""Keep the mood display and scene recommendation on one analysis result."""
from shared.director import understand
import os

def preview_mood(plan, reviewed):
    original = plan.get('detected_lyrics', '')
    creative = plan.get('creative')
    ai_configured = bool(os.environ.get('OPENAI_API_KEY', '').strip()) and os.environ.get('LYRIC_MOOD_AI','true').lower() not in {'false','0','off'}
    # An old backend mood must not bypass configured semantic analysis.
    use_backend = not ai_configured or (creative or {}).get('mood_method') == 'semantic_ai'
    if use_backend and reviewed.split() == original.split() and isinstance(creative, dict) and creative.get('mood'):
        result = dict(creative)
        result.setdefault('mood_reason', 'Using the song mood returned by the backend analysis.')
        result.setdefault('mood_method', 'backend_analysis')
        return result
    return understand(reviewed, plan.get('timeline', {}))
