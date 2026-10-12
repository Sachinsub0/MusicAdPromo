import unittest
from shared.director import understand
from shared.templates import recommend

class MoodTests(unittest.TestCase):
    def pick(self, lyrics, energy=.95):
        timeline = {'energy': energy}
        creative = understand(lyrics, timeline)
        return creative, recommend(creative, timeline, lyrics)

    def test_heartbreak_overrides_loud_audio_and_car_mentions(self):
        creative, scene = self.pick('I drive alone, you left me crying with a broken heart')
        self.assertEqual(scene, 'river_skyline')
        self.assertEqual(creative['primary_mood'], 'melancholic')
        self.assertEqual(creative['mood_source'], 'lyrics')

    def test_romance_on_loud_audio(self):
        self.assertEqual(self.pick('I love you, hold me close and kiss me')[1], 'dreamscape')

    def test_confidence_on_quiet_audio(self):
        self.assertEqual(self.pick('Getting paid, I made it, winning on top', .1)[1], 'racecars')

    def test_party_and_hope(self):
        self.assertEqual(self.pick('Dance and celebrate all night')[1], 'racecars')
        self.assertEqual(self.pick('Better days, healing, find my peace')[1], 'dreamscape')

    def test_punctuation_contractions_and_negation(self):
        creative, scene = self.pick('She doesn’t love me! I miss you.')
        self.assertEqual(scene, 'river_skyline')
        self.assertEqual(creative['lyric_scores']['romantic'], 0)
        creative, _ = self.pick("I'm not sad, never lonely. Happy, dance and celebrate!")
        self.assertEqual(creative['lyric_scores']['melancholic'], 0)
        self.assertEqual(creative['primary_mood'], 'celebratory')

    def test_corrected_lyrics_override_stale_plan(self):
        self.assertEqual(recommend({'mood': ['energetic']}, {'energy': .9},
                                   'You left me with a broken heart'), 'river_skyline')

    def test_empty_unknown_and_non_english_fallback(self):
        for lyrics in ['', 'the table is over there', 'こんにちは']:
            creative, scene = self.pick(lyrics)
            self.assertEqual(creative['mood_source'], 'audio_fallback')
            self.assertEqual(scene, 'racecars')
        self.assertEqual(self.pick('', .1)[1], 'river_skyline')

if __name__ == '__main__':
    unittest.main()
