import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {getScenario} from '../lib/server-data';
import {createGame,autoComplete} from '../lib/engine';
const read=(p:string)=>JSON.parse(readFileSync(p,'utf8'));
const digest=(value:unknown)=>createHash('sha256').update(JSON.stringify(value)).digest('hex');
const manifest=read('data/clean/reference_identity_corrections_2021.json');
const source=read('data/processed/scenario-2021.json');
const model=read('analytics/model-2021.json');

test('2021 historical pick 3 resolves only to the existing eligible Trey Lance identity',()=>{
    assert.deepEqual(source.actualPicks.find((p:{overall:number})=>p.overall===3),{overall:3,round:1,team:'SF',prospectId:'p2021-4a3e07404f'});
    const lance=source.prospects.filter((p:{name:string})=>p.name==='Trey Lance');
    assert.equal(lance.length,1);assert.equal(lance[0].id,'p2021-4a3e07404f');assert.equal(lance[0].playable,true);
    assert.equal(source.prospects.some((p:{id:string})=>p.id==='p2021-ref-e9aacb6df1'),false);
    assert.equal(model.projections.some((p:{prospectId:string})=>p.prospectId==='p2021-ref-e9aacb6df1'),false);
    assert.equal(source.metadata.playableProspectCount,323);assert.equal(source.metadata.referenceOnlyProspectCount,82);
    assert.equal(read('data/clean/audited_postdraft_reference_aliases.json').aliases.length,1);
});

test('reference correction preserves eligible scouting rows, unrelated references, numeric projections and other years byte for byte',()=>{
    const i=manifest.invariants;
    assert.equal(digest(source.prospects.filter((p:{playable:boolean})=>p.playable)),i.playableProspectsSha256);
    assert.equal(digest(source.prospects.filter((p:{playable:boolean})=>!p.playable)),i.otherReferenceProspectsSha256);
    assert.equal(digest(source.actualPicks.filter((p:{overall:number})=>p.overall!==3)),i.otherActualPicksSha256);
    for(const section of ['teams','picks','games'])assert.equal(digest(source[section]),i[section+'Sha256']);
    assert.equal(digest(model.projections.map((p:Record<string,unknown>)=>Object.fromEntries(Object.entries(p).filter(([k])=>k!=='modelVersion')))),i.projectionValuesSha256);
    for(const [file,hash]of Object.entries(i.otherYearFiles))assert.equal(createHash('sha256').update(readFileSync(file)).digest('hex'),hash,file);
});

test('2021 production entry uses corrected pinned versions and finishes a normal eligible draft',()=>{
    const {dataset,models}=getScenario(2021);
    const game=createGame({year:2021,team:'SF',seed:'trey-reference-regression',modelVersion:String(models.version),now:'2026-11-20T00:00:00Z'},dataset);
    assert.equal(game.datasetVersion,manifest.scenarioVersion);
    assert.notEqual(game.datasetVersion,'nflverse-2021-combine-pool-v1');
    assert.ok(String(models.version).startsWith(manifest.modelVersion+'+'));
    assert.notEqual(models.version,'redraft-2021-pre2018-logistic-C10-v1+blind-g5-v1+nflverse-2021-combine-pool-v1');
    const complete=autoComplete(game,dataset,models);
    assert.equal(complete.status,'ready');assert.equal(complete.selections.length,259);
    assert.equal(new Set(complete.selections.map(s=>s.prospectId)).size,259);
    const playable=new Set(dataset.prospects.filter(p=>p.eligibilitySource==='combine-participant').map(p=>p.id));
    assert.ok(complete.selections.every(s=>playable.has(s.prospectId)));
    assert.equal(createHash('sha256').update(readFileSync('data/processed/scenario-2021.json')).digest('hex'),manifest.scenarioSha256);
    assert.equal(createHash('sha256').update(readFileSync('analytics/model-2021.json')).digest('hex'),manifest.modelSha256);
});
