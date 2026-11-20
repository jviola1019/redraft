#!/usr/bin/env python3
"""Reproduce one audited reference-identity correction without refetching history.

The old version is read from git, hash-guarded by the primary-source audit. This
preserves unrelated source facts because the original order/invitee text captures
are missing and rebuilding against refreshed games would change unrelated data.
"""
import copy
import hashlib
import json
import subprocess
from pathlib import Path
from reference_aliases import ALIAS_PATH, ROOT, VERSION_2021, MODEL_VERSION_2021, load_aliases, resolve_alias
BASE = '2c632fb'
SCENARIO = 'data/processed/scenario-2021.json'
MODEL = 'analytics/model-2021.json'
def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def old_bytes(path):return subprocess.check_output(['git','show',f'{BASE}:{path}'],cwd=ROOT)
def encode(value,compact=False):return (json.dumps(value,separators=(',',':')) if compact else json.dumps(value,indent=2)).encode()+b'\n'
def generate():
    evidence=json.loads(ALIAS_PATH.read_text());a=load_aliases(2021)[0]
    original=old_bytes(SCENARIO)
    if sha_bytes(original)!=evidence['expectedInput']['scenarioSha256']:raise ValueError('Audited original scenario hash mismatch')
    base=json.loads(original);new=copy.deepcopy(base)
    import csv
    with (ROOT/'data/raw/draft_picks.csv').open(newline='')as f:
        row=next(r for r in csv.DictReader(f)if r['season']=='2021'and r['pick']=='3')
    target=resolve_alias(2021,row,base['prospects'],[a]);assert target==a['toCanonicalProspectId']
    pick=next(p for p in new['actualPicks']if p['overall']==3)
    if pick!=a['expectedHistoricalSelection']:raise ValueError('Original historical selection guard mismatch')
    pick['prospectId']=target
    removed=[p for p in new['prospects']if p['id']==a['fromProspectId']]
    if len(removed)!=1 or removed[0]['playable']is not False:raise ValueError('Only the audited reference-only identity can be removed')
    new['prospects']=[p for p in new['prospects']if p['id']!=a['fromProspectId']]
    new['metadata']['version']=VERSION_2021
    new['metadata']['referenceOnlyProspectCount']-=1
    alias_source={'path':str(ALIAS_PATH.relative_to(ROOT)),'url':'audited postdraft reference identity only; never pre-draft features','sha256':sha_bytes(ALIAS_PATH.read_bytes())}
    new['metadata']['sourceFiles'].append(alias_source)
    # This key is also emitted by a future full source rebuild.
    correction={'version':'trey-lance-reference-v1','auditedOn':'2026-11-20','aliasArtifact':str(ALIAS_PATH.relative_to(ROOT)),'aliasesApplied':1,'scope':'Postdraft historical identity references only; eligible pool and all scouting features unchanged.'}
    new['metadata']['referenceIdentityCorrection']=correction
    scenario_bytes=encode(new,compact=True)
    model=json.loads(old_bytes(MODEL));old_model_version=model['version']
    model['version']=MODEL_VERSION_2021;model['scenarioVersion']=VERSION_2021
    model['projections']=[p for p in model['projections']if p['prospectId']!=a['fromProspectId']]
    for p in model['projections']:p['modelVersion']=p['modelVersion'].replace(old_model_version,MODEL_VERSION_2021,1)
    model['counts']['scenarioProspects']-=1;model['counts']['referenceOnlyPositionFallbacks']-=1
    model['scenarioProvenance']['sourceFiles']=new['metadata']['sourceFiles']
    model['sourceHashes'][SCENARIO]=sha_bytes(scenario_bytes)
    model_bytes=encode(model)
    manifest={'schemaVersion':1,'version':'trey-lance-reference-regeneration-v1','baseCommit':BASE,'auditedOn':'2026-11-20','aliasArtifact':alias_source,'oldScenarioSha256':sha_bytes(original),'scenarioVersion':VERSION_2021,'scenarioSha256':sha_bytes(scenario_bytes),'oldModelSha256':sha_bytes(old_bytes(MODEL)),'modelVersion':MODEL_VERSION_2021,'modelSha256':sha_bytes(model_bytes),'correctedOverall':3,'fromProspectId':a['fromProspectId'],'toCanonicalProspectId':target,'playableProspects':323,'referenceOnlyProspects':82,'scoutingFeaturesChanged':False,'otherYearsChanged':False,'sourceRebuildLimitations':['Original2021 order and invitee webtext captures are unavailable locally.','Full current raw-source rebuild also changes unrelated games/source hashes; this correction preserves the audited base snapshot.'],'regenerationMethod':'Exact audited alias at the reference join boundary, reproduced as a hash-guarded minimal change from the immutable prior scenario/model. Numeric model predictions are preserved.'}
    def js_numbers(value):
        if isinstance(value,float)and value.is_integer():return int(value)
        if isinstance(value,list):return [js_numbers(v)for v in value]
        if isinstance(value,dict):return {k:js_numbers(v)for k,v in value.items()}
        return value
    digest_json=lambda value:sha_bytes(json.dumps(js_numbers(value),separators=(',',':'),ensure_ascii=False).encode())
    manifest['invariants']={
        'playableProspectsSha256':digest_json([p for p in base['prospects']if p['playable']]),
        'otherReferenceProspectsSha256':digest_json([p for p in base['prospects']if not p['playable'] and p['id']!=a['fromProspectId']]),
        'otherActualPicksSha256':digest_json([p for p in base['actualPicks']if p['overall']!=3]),
        'teamsSha256':digest_json(base['teams']),'picksSha256':digest_json(base['picks']),'gamesSha256':digest_json(base['games']),
        'projectionValuesSha256':digest_json([{k:v for k,v in p.items()if k!='modelVersion'}for p in json.loads(old_bytes(MODEL))['projections']if p['prospectId']!=a['fromProspectId']]),
        'otherYearFiles':{p:sha_bytes(old_bytes(p))for year in range(2018,2027)if year!=2021 for p in ([f'data/processed/scenario-{year}.json']+([f'analytics/model-{year}.json']if year>2018 else ['analytics/model.json']))},
    }
    return {SCENARIO:scenario_bytes,MODEL:model_bytes,'data/clean/reference_identity_corrections_2021.json':encode(manifest)}
def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    outputs=generate()
    if args.check:
        different=[p for p,b in outputs.items()if (ROOT/p).read_bytes()!=b]
        if different:raise SystemExit('Regeneration mismatch: '+', '.join(different))
    else:
        for p,b in outputs.items():(ROOT/p).write_bytes(b)
    print(json.dumps({'artifacts':list(outputs),'reproducible':True,'checkOnly':args.check}))
if __name__=='__main__':main()
