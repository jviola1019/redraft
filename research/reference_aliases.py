"""Exact audited postdraft reference joins, never prospect eligibility or features."""
import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
ALIAS_PATH = ROOT / 'data/clean/audited_postdraft_reference_aliases.json'
VERSION_2021 = 'nflverse-2021-combine-pool-v2-trey-reference'
MODEL_VERSION_2021 = 'redraft-2021-pre2018-logistic-C10-v2-trey-reference'

def load_aliases(year):
    if year != 2021:
        return []
    artifact = json.loads(ALIAS_PATH.read_text())
    aliases = artifact['aliases']
    if artifact['schemaVersion'] != 1 or artifact['status'] != 'approved-for-versioned-reference-regeneration' or len(aliases) != 1:
        raise ValueError('Re-audit changed postdraft reference alias scope')
    a = aliases[0]
    if (a['aliasId'] != 'trey-lance-2021-reference-identity-v1' or a['draftYear'] != 2021
        or a['decision'] != 'audited-same-person' or a['preDraftFeatureAllowed'] is not False
        or a['eligibilityInferenceAllowed'] is not False or a['measurementMergeAllowed'] is not False
        or a['projectionMutationAllowed'] is not False):
        raise ValueError('Reference aliases cannot modify pre-draft information')
    raw = ROOT / artifact['expectedInput']['rawDraftPath']
    if hashlib.sha256(raw.read_bytes()).hexdigest() != artifact['expectedInput']['rawDraftSha256']:
        raise ValueError('Raw draft input changed; re-audit the exact reference alias')
    return aliases

def resolve_alias(year, row, prospects, aliases):
    matches = [a for a in aliases if a['draftYear'] == year
               and a['externalIdentity']['pfrPlayerId'] == row['pfr_player_id']]
    if not matches:
        return None
    if len(matches) != 1:
        raise ValueError('Ambiguous audited reference alias')
    a = matches[0]
    expected = a['expectedHistoricalSelection']
    if (int(row['pick']) != expected['overall'] or int(row['round']) != expected['round']
        or row['team'] != 'SFO' or expected['team'] != 'SF'
        or row['gsis_id'] != a['externalIdentity']['gsisId']
        or row['pfr_player_name'] != a['canonicalName'] or row['position'] != 'QB'
        or row['college'] != a['referenceSchoolAlias']):
        raise ValueError('Audited draft identity guard changed')
    target = [p for p in prospects if p['id'] == a['toCanonicalProspectId']]
    if len(target) != 1:
        raise ValueError('Audited alias target must already exist in the eligible pool')
    p = target[0]
    if (p['name'] != a['canonicalName'] or p['college'] != a['canonicalSchool']
        or p['position'] != 'QB' or p['eligibilitySource'] != 'combine-participant'
        or p['playable'] is not True):
        raise ValueError('Audited alias cannot create or reinterpret an eligible prospect')
    return p['id']
