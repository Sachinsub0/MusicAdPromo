import unittest
from unittest.mock import patch
from shared.preview import preview_mood
from shared.templates import recommend

class PreviewTests(unittest.TestCase):
 @patch('shared.preview.understand')
 def test_backend_mood_used_for_unedited_lyrics(self, analyze):
  for moods, scene in [(['energetic','confident','kinetic'],'racecars'),(['romantic','longing','dreamy'],'dreamscape')]:
   plan={'detected_lyrics':'unfamiliar words','creative':{'mood':moods},'timeline':{}}
   result=preview_mood(plan,'unfamiliar  words')
   self.assertEqual(result['mood'],moods)
   self.assertEqual(recommend(result,{}),scene)
  analyze.assert_not_called()
 @patch('shared.preview.understand')
 def test_edits_reanalyzed(self, analyze):
  analyze.return_value={'mood':['melancholic']}
  result=preview_mood({'detected_lyrics':'old words','creative':{'mood':['confident']},'timeline':{}},'new words')
  analyze.assert_called_once_with('new words',{})
  self.assertEqual(result['mood'],['melancholic'])
 @patch('shared.preview.understand')
 def test_missing_analysis(self, analyze):
  preview_mood({'detected_lyrics':'words'},'words')
  analyze.assert_called_once()
