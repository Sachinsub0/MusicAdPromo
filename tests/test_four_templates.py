import os, unittest
from unittest.mock import patch
from shared.preview import preview_mood
from shared.templates import TEMPLATES, recommend, frame

class FourTemplatesTests(unittest.TestCase):
 def test_primary_mood_mapping(self):
  self.assertEqual(set(TEMPLATES),{'racecars','dreamscape','river_skyline','sunset_coast'})
  for mood,scene in [('dark','racecars'),('confident','racecars'),('melancholic','dreamscape'),('dreamy','dreamscape'),('romantic','sunset_coast'),('celebratory','sunset_coast'),('moody','river_skyline')]:
   self.assertEqual(recommend({'primary_mood':mood},{}),scene)
 def test_every_scene_animates(self):
  for name in TEMPLATES:
   self.assertEqual(frame(name,0).size,(540,960))
   self.assertNotEqual(frame(name,0).tobytes(),frame(name,1.5).tobytes())
 @patch.dict(os.environ,OPENAI_API_KEY='test',LYRIC_MOOD_AI='true')
 @patch('shared.preview.understand')
 def test_ai_still_replaces_legacy_backend_result(self, analyze):
  analyze.return_value={'mood_method':'semantic_ai'}
  result=preview_mood({'detected_lyrics':'hello','creative':{'mood':['moody']}},'hello')
  self.assertEqual(result['mood_method'],'semantic_ai')
