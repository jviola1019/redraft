import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from analyze import analyze


class TrialChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.directory = Path(cls.temp.name)
        subprocess.run(['node', str(Path(__file__).with_name('prepare.mjs')), cls.temp.name], check=True)
        cls.key = json.loads((cls.directory / 'key.json').read_text())

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_forms_are_complementary_and_answers_separate(self):
        forms = []
        for letter in 'AB':
            html = (self.directory / f'form-{letter}.html').read_text()
            for pair in self.key['pairs']:
                for name in pair['names']:
                    self.assertNotIn(name, html)
            forms.append(json.loads(re.search(r'const config=(.*);', html)[1]))
        self.assertEqual(forms[0]['keyId'], forms[1]['keyId'])
        for a,b in zip(forms[0]['items'], forms[1]['items']):
            self.assertNotEqual(bool(a['colleges']), bool(b['colleges']))
            self.assertEqual({k:v for k,v in a.items() if k!='colleges'}, {k:v for k,v in b.items() if k!='colleges'})

    def test_scoring_and_duplicate_detection(self):
        # Artificial responses for test arithmetic only.
        people = []
        for form in 'AB':
            rows = [{'item':p['item'], 'choice':0, 'guesses':(p['names'] if p['item']%2==(form=='A') else ['', ''])}
                    for p in self.key['pairs']]
            people.append({'study':self.key['study'], 'keyId':self.key['keyId'], 'form':form, 'experience':'closely',
                           'participant':form.lower()*32, 'responses':rows})
        self.assertEqual(analyze(self.key,people)['equalPairRecognitionDifference'],1)
        self.assertIsNone(analyze(self.key,people[:1])['equalPairRecognitionDifference'])
        self.assertEqual(analyze(self.key,[])['participants'],0)
        with self.assertRaises(ValueError):
            analyze(self.key,people*2)
