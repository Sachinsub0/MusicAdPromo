import os, unittest
from unittest.mock import patch
from urllib.error import URLError
from shared.preview import preview_mood
from shared.templates import recommend, TEMPLATES
from shared.mood import _semantic_analysis
import test_semantic_mood

class BaselineTests(unittest.TestCase):
 def test_aggressive_and_sad_same_scene_distinct_moods(self):
  for primary in ['dark','confident','melancholic']:
   self.assertEqual(recommend({'primary_mood':primary},{'tempo_bpm':180}),'dreamscape')
  self.assertNotIn('racecars',TEMPLATES)
 @patch.dict(os.environ,OPENAI_API_KEY='test',LYRIC_MOOD_AI='true')
 @patch('shared.preview.understand')
 def test_legacy_mood_does_not_skip_ai(self, analyze):
  analyze.return_value={'mood_method':'semantic_ai'}
  result=preview_mood({'detected_lyrics':'hello','creative':{'mood':['moody']}},'hello')
  self.assertEqual(result['mood_method'],'semantic_ai')
  analyze.assert_called_once()
 @patch('shared.mood.time.sleep')
 @patch('shared.mood.urlopen')
 def test_transient_retry(self, call, sleep):
  _semantic_analysis.cache_clear()
  call.side_effect=[URLError('temporary'),test_semantic_mood.SemanticTests().response()]
  self.assertEqual(_semantic_analysis('empty bed','test-model','test-key')[0],'melancholic')
  self.assertEqual(call.call_count,2)
  _semantic_analysis.cache_clear()
