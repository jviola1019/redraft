"""Reproduce finite-cohort identity linkage risks and audit the actual runtime policy.
These are deterministic counts, not estimates of human recognition or anonymity.
Run: python analytics/identity_audit.py
"""
from collections import Counter
from pathlib import Path
import hashlib
import json
import math
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/processed/scenario-2018.json'
data = json.loads(DATA.read_text())
prospects = [p for p in data['prospects'] if p.get('eligibilitySource') == 'combine-participant']
fields = ['heightIn', 'weightLb', 'forty', 'bench', 'verticalIn', 'broadJumpIn', 'cone', 'shuttle']
widths = dict(zip(fields, [3, 15, .2, 5, 5, 10, .2, .2]))

def counts(keys):
    counts = Counter(keys)
    n = sum(counts.values())
    return {'n': n, 'distinctProfiles': len(counts), 'singletonProspects': sum(v for v in counts.values() if v == 1),
            'singletonFraction': sum(v for v in counts.values() if v == 1) / n,
            'prospectsInGroupsBelowFive': sum(v for v in counts.values() if v < 5),
            'minimumProfileGroup': min(counts.values()), 'maximumProfileGroup': max(counts.values()),
            'profileSizeDistribution': dict(sorted(Counter(counts.values()).items()))}

def exact(columns):
    return counts(tuple(p.get(f) for f in columns) for p in prospects)

def band(value, width):
    return None if value is None else math.floor(value / width + .5)

metrics = {
    'collegeAndExactPosition': exact(['college', 'position']),
    'exactPositionHeightWeight': exact(['position', 'heightIn', 'weightLb']),
    'exactPositionFortyVerticalBroad': exact(['position', 'forty', 'verticalIn', 'broadJumpIn']),
    'exactPositionCollegeHeightWeightForty': exact(['position', 'college', 'heightIn', 'weightLb', 'forty']),
    'exactPositionAllMeasurements': exact(['position'] + fields),
    'exactPositionAllIndividuallyCoarsenedMeasurements': counts(tuple([p['position']] + [band(p.get(f), widths[f]) for f in fields]) for p in prospects),
}
# Execute production TypeScript, avoiding a second implementation of grouping.
js = r'''
import fs from 'node:fs';import os from 'node:os';import path from 'node:path';import {createRequire} from 'node:module';import ts from 'typescript';
const dir=fs.mkdtempSync(path.join(os.tmpdir(),'redraft-identity-'));
try {
 fs.mkdirSync(path.join(dir,'lib'));fs.symlinkSync(path.resolve('data'),path.join(dir,'data'),'dir');fs.writeFileSync(path.join(dir,'package.json'),'{{"type":"commonjs"}}'.replace('{{','{').replace('}}','}'));
 for(const n of ['types','engine','scouting'])fs.writeFileSync(path.join(dir,'lib',n+'.js'),ts.transpileModule(fs.readFileSync('lib/'+n+'.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,esModuleInterop:true}}).outputText);
 const require=createRequire(import.meta.url),s=require(path.join(dir,'lib/scouting.js')),e=require(path.join(dir,'lib/engine.js'));
 const data=JSON.parse(fs.readFileSync('data/processed/scenario-2018.json')),models=JSON.parse(fs.readFileSync('analytics/model.json')),policy=s.createScoutingPolicy(data,models),aliases=await s.aliasCatalog('audit-only-salt-not-used-by-production',data),game=e.createGame({seed:'identity-audit',now:'2026-11-02T00:00:00Z'},data);
 game.scouted=data.prospects.filter(e.isPlayableProspect).map(p=>p.id);
 const views=s.prospectViews(game,data,models,policy,aliases);
 console.log(JSON.stringify({audit:policy.audit,profiles:views.map(({id,name,blindName,scouted,...evidence})=>({...evidence,projection:{...evidence.projection,prospectId:undefined}}))}));
} finally { fs.rmSync(dir,{recursive:true,force:true}); }
'''
run = subprocess.run(['node', '--input-type=module', '-e', js], cwd=ROOT, capture_output=True, text=True, check=True)
runtime = json.loads(run.stdout)
metrics['runtimeFullCumulativeEvidenceWithoutOpaqueLabels'] = counts(json.dumps(p, sort_keys=True) for p in runtime['profiles'])
assert metrics['runtimeFullCumulativeEvidenceWithoutOpaqueLabels']['minimumProfileGroup'] >= 5
report = {
    'version': 'identity-audit-v2', 'asOf': '2026-11-02', 'datasetVersion': data['metadata'].get('version'),
    'cohort': '2018, verified playable combine participants only', 'n': len(prospects),
    'method': 'Exact equality of joint released fields; null is a category. Individually coarsened rule: floor(value/width+0.5). Runtime count uses every fully-scouted browser field except opaque labels and user action state.',
    'individualBandWidths': widths, 'metrics': metrics, 'runtimePolicy': runtime['audit'],
    'hashes': {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['lib/scouting.ts', 'analytics/model.json', 'data/processed/scenario-2018.json']},
    'limitations': [
        'Cohort uniqueness is not the probability that a human recognizes a player.',
        'At least five matching initial profiles does not guarantee protection against elimination, auxiliary information, inferred group membership, repeat-run reveals or collusion.',
        'Same private daily alias salt enables standardized play but allows shared spoiler dictionaries after any completed attempt.',
        'Opaque aliases protect direct canonical-ID lookup only; they do not erase football knowledge.',
        'Grouped measurements describe known values in the group; an individual member may not have completed a measurement.',
        'Utility and recognition require separate validation. No human recognition experiment has yet been executed.',
    ],
}
output = ROOT/'analytics/identity_audit.json'
output.write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps({'n': len(prospects), 'metrics': metrics, 'runtimePolicy': runtime['audit']}, indent=2))
