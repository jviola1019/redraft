import copy
import csv
import json
import unittest
from unittest.mock import patch
from reference_aliases import ROOT, load_aliases, resolve_alias

class ReferenceAliasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scenario=json.loads((ROOT/'data/processed/scenario-2021.json').read_text())
        cls.aliases=load_aliases(2021)
        with (ROOT/'data/raw/draft_picks.csv').open(newline='')as f:
            cls.row=next(r for r in csv.DictReader(f)if r['season']=='2021'and r['pick']=='3')
    def test_exact_reference_join(self):
        self.assertEqual(resolve_alias(2021,self.row,self.scenario['prospects'],self.aliases),'p2021-4a3e07404f')
        self.assertEqual(load_aliases(2020),[])
        changed=copy.deepcopy(self.row);changed['pfr_player_id']='unreviewed'
        self.assertIsNone(resolve_alias(2021,changed,self.scenario['prospects'],self.aliases))
    def test_guarded_identity_and_existing_target(self):
        for key,value in [('college','Ohio St.'),('pick','11'),('gsis_id','wrong'),('team','NYJ')]:
            with self.subTest(field=key):
                changed=copy.deepcopy(self.row);changed[key]=value
                with self.assertRaises(ValueError):resolve_alias(2021,changed,self.scenario['prospects'],self.aliases)
        with self.assertRaises(ValueError):resolve_alias(2021,self.row,[],self.aliases)
    def test_source_builder_applies_only_reviewed_reference_alias(self):
        import build_scenarios as b
        pins={str(ROOT/r['path']):r['sha256']for r in self.scenario['metadata']['sourceFiles']}
        real=b.digest
        # Missing old text captures are not re-created or treated as fetched bytes.
        # These retained pins permit exercising identity ingestion independently of
        # full-source reconstruction, which intentionally differs in game history.
        def retain_missing_pin(path):return real(path)if path.exists()else pins[str(path)]
        with patch.object(b,'digest',side_effect=retain_missing_pin):rebuilt,_=b.build_scenario(2021)
        for section in ['prospects','actualPicks','picks','teams']:
            self.assertEqual(rebuilt[section],self.scenario[section],section)
        self.assertEqual(rebuilt['metadata']['referenceIdentityCorrection'],self.scenario['metadata']['referenceIdentityCorrection'])

if __name__=='__main__':unittest.main(verbosity=2)
