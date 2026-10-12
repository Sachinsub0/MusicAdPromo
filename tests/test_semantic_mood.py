import io, json, os, unittest
from unittest.mock import patch
from shared.mood import analyze_lyrics, _semantic_analysis

class SemanticTests(unittest.TestCase):
 def setUp(self):
  _semantic_analysis.cache_clear()
  self.env=patch.dict(os.environ,OPENAI_API_KEY='test',LYRIC_MOOD_AI='true')
  self.env.start()
 def tearDown(self):
  self.env.stop();_semantic_analysis.cache_clear()
 def response(self, primary='melancholic', confidence=.9):
  data=dict(primary_mood=primary,secondary_mood=None,confidence=confidence,reason='The narrator mourns a relationship.',evidence=['empty bed','invented quote'])
  return io.StringIO(json.dumps({'choices':[{'message':{'content':json.dumps(data)}}]}))
 @patch('shared.mood.urlopen')
 def test_context_cache_edits_and_evidence(self, call):
  call.side_effect=lambda *a,**k:self.response()
  for _ in range(2):
   result=analyze_lyrics('Gucci on the empty bed')
   self.assertEqual(result['mood_method'],'semantic_ai')
   self.assertEqual(result['semantic_evidence'],['empty bed'])
  self.assertEqual(call.call_count,1)
  analyze_lyrics('new words');self.assertEqual(call.call_count,2)
 @patch('shared.mood.urlopen')
 def test_invalid_result_retries_and_falls_back(self, call):
  call.side_effect=lambda *a,**k:self.response('invalid')
  for _ in range(2):
   result=analyze_lyrics('Getting paid on top')
   self.assertEqual(result['primary_mood'],'confident')
   self.assertIn('unavailable',result['mood_notice'])
  self.assertEqual(call.call_count,2)
 @patch('shared.mood.urlopen',side_effect=TimeoutError)
 def test_timeout(self, call):
  self.assertEqual(analyze_lyrics('You walked away')['primary_mood'],'melancholic')
 @patch('shared.mood.urlopen')
 def test_disabled_empty_and_missing_key(self, call):
  analyze_lyrics('')
  with patch.dict(os.environ,OPENAI_API_KEY=''):
   self.assertEqual(analyze_lyrics('Louis V, iced out')['primary_mood'],'confident')
  with patch.dict(os.environ,LYRIC_MOOD_AI='false'):
   analyze_lyrics('Hello')
  call.assert_not_called()
 @patch('shared.mood.urlopen')
 def test_uncertain(self, call):
  call.return_value=self.response(confidence=.2)
  self.assertEqual(analyze_lyrics('Getting paid')['mood_method'],'offline_rules')
