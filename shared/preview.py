"""Keep the mood display and scene recommendation on one analysis result."""
from shared.director import understand

def preview_mood(plan, reviewed):
    original = plan.get('detected_lyrics', '')
    creative = plan.get('creative')
    if reviewed.split() == original.split() and isinstance(creative, dict) and creative.get('mood'):
        result = dict(creative)
        result.setdefault('mood_reason', 'Using the song mood returned by the backend analysis.')
        result.setdefault('mood_method', 'backend_analysis')
        return result
    return understand(reviewed, plan.get('timeline', {}))
