import unittest
from unittest.mock import patch
import sys, types
from shared.alignment import complete_words, preview_corrections, align_words
from shared.templates import recommend, frame
class AlignmentTests(unittest.TestCase):
 def test_insertion_deletion_and_punctuation(self):
  raw=[{'word':'I','start':.2,'end':.4},{'word':'love','start':.5,'end':.8},{'word':'you','start':1.,'end':1.3}]
  for text in ['I really love you!','I you','I adore you','I I love you','Été 2026 💜']:
   result=preview_corrections(raw,text,2)
   self.assertEqual([w['word'] for w in result],text.split())
   self.assertTrue(all(0<=w['start']<=w['end']<=2 for w in result))
   self.assertTrue(all(a['end']<=b['start'] for a,b in zip(result,result[1:])))
 def test_untimed_tokens_retained(self):
  result=complete_words('love 2026 you',[{'word':'love','start':.2,'end':.5},{'word':'2026'},{'word':'you','start':1.,'end':1.2}],2)
  self.assertEqual(len(result),3);self.assertTrue(result[1]['estimated']);self.assertFalse(result[0]['estimated'])
 def test_forced_aligner_receives_corrected_text(self):
  capture=[]
  def align(segments,*args,**kwargs):
   capture.extend(segments)
   return {'word_segments':[{'word':'new','start':.3,'end':.6},{'word':'words','start':.7,'end':1.}]}
  fake=types.SimpleNamespace(load_audio=lambda _:[],load_model=lambda *a,**k:types.SimpleNamespace(transcribe=lambda *a,**k:{'segments':[{'text':'wrong lyric','start':0,'end':2}],'language':'en'}),load_align_model=lambda **k:(None,None),align=align)
  with patch.dict(sys.modules,{'whisperx':fake,'torch':types.SimpleNamespace(cuda=types.SimpleNamespace(is_available=lambda:False))}),patch('shared.alignment.subprocess.run'),patch('shared.alignment._separate_vocals',return_value=('fake','disabled')):
   rows,meta=align_words('fake',0,2,'new words added')
  self.assertEqual(capture[0]['text'],'new words added');self.assertEqual([w['word'] for w in rows],['new','words','added']);self.assertTrue(rows[-1]['estimated'])
 def test_template_routing_and_animation(self):
  self.assertEqual(recommend({'mood':['energetic']},{},''),'racecars')
  self.assertEqual(recommend({'mood':['romantic']},{},''),'dreamscape')
  self.assertEqual(recommend({'mood':['dark']},{},''),'river_skyline')
  for name in ['river_skyline','racecars','dreamscape']:
   self.assertNotEqual(frame(name,0).tobytes(),frame(name,1).tobytes())
if __name__=='__main__':unittest.main()
