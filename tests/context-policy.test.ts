import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {createUsagePolicy,priorUsageAdjustment,PRIOR_USAGE_CAP,createGame,draftUtility,autoComplete,rankLeaderboard,validateScoringRecalibration} from '../lib/engine';
import type {Dataset,PriorSeasonContextDataset} from '../lib/types';
const context=JSON.parse(readFileSync('data/clean/team_context_2018.json','utf8')) as PriorSeasonContextDataset;
const manifest=JSON.parse(readFileSync('data/clean/team_context_source_manifest.json','utf8'));
const dataset=JSON.parse(readFileSync('data/processed/scenario-2018.json','utf8')) as Dataset;
const models=JSON.parse(readFileSync('analytics/model.json','utf8'));
const cutoff=String(dataset.metadata.informationCutoff);
const policy=createUsagePolicy(context,cutoff,manifest.artifactSha256);
const copy=()=>JSON.parse(JSON.stringify(context)) as PriorSeasonContextDataset;
const game=createGame({team:'CLE',seed:'usage-policy-test',now:'2026-11-04T00:00:00Z'},dataset);
test('runtime context fingerprint matches all source bytes and covers 32 prior-season teams',()=>{
  const actual=createHash('sha256').update(readFileSync('data/clean/team_context_2018.json')).digest('hex');
  assert.equal(manifest.artifactSha256,actual);assert.equal(policy.sourceSha256,actual);assert.equal(context.teams.length,32);
  assert.equal(new Set(context.teams.map(t=>t.teamId)).size,32);assert.ok(context.teams.every(t=>t.priorSeason===2017&&t.regularGames===16));
  assert.ok(context.teams.every(t=>t.scheme===null&&t.draftDayRoster===null&&t.draftDayCoaches===null&&t.rosterContinuity===null));
});
test('all utility adjustments are finite and strictly bounded with specials unsupported',()=>{
  const values=Object.values(policy.positionAdjustments).flatMap(Object.values);assert.ok(values.some(v=>v>0));assert.ok(values.some(v=>v<0));assert.ok(values.every(v=>Number.isFinite(v)&&Math.abs(v)<=PRIOR_USAGE_CAP));
  assert.ok(Object.values(policy.leagueReferences).every(v=>v.teams===32));
  const specialist=dataset.prospects.find(p=>p.position==='K')!;assert.equal(priorUsageAdjustment(game,specialist,'CLE',{...models,usagePolicy:policy}),0);
});
test('later or invalid observation dates and unidentified artifacts fail closed',()=>{
  for(const value of ['2019-01-01','invalid']){const altered=copy();altered.teams[0].observedThrough=value;assert.throws(()=>createUsagePolicy(altered,cutoff,manifest.artifactSha256),/cutoff/);}
  const later=copy();later.metadata.observedSeason=2018;assert.throws(()=>createUsagePolicy(later,cutoff,manifest.artifactSha256),/season/);
  const group=copy();group.teams[0].groups[0].observedSeason=2020;assert.throws(()=>createUsagePolicy(group,cutoff,manifest.artifactSha256),/later season/);
  assert.throws(()=>createUsagePolicy(context,cutoff,'not-a-hash'),/SHA256/);
  const p=dataset.prospects.find(p=>p.position==='QB')!;
  assert.throws(()=>priorUsageAdjustment(game,p,'CLE',{usagePolicy:{...policy,informationCutoff:'invalid'}}),/cutoff/);
});
test('unknown coverage is neutral rather than silently imputed as zero usage',()=>{
  const altered=copy();const row=altered.teams[0].groups.find(g=>g.group==='WR')!;row.totalScrimmageSnaps=null;row.complete=false;
  const result=createUsagePolicy(altered,cutoff,manifest.artifactSha256);
  for(const values of Object.values(result.positionAdjustments))for(const position of ['QB','RB','WR','TE','OL'])assert.equal(values[position],0);
  assert.equal(result.leagueReferences.WR.teams,31);
});
test('ordering, coach names and descriptive contributor counts cannot masquerade as need',()=>{
  const altered=copy();altered.teams.reverse();for(const t of altered.teams){t.groups.reverse();t.priorHeadCoaches=[{name:'Test fixture coach',games:16}];for(const group of t.groups){group.players200Plus=999;group.positiveSnapPlayers=999;group.largestPlayerShare=.999;}}
  assert.deepEqual(createUsagePolicy(altered,cutoff,manifest.artifactSha256).positionAdjustments,policy.positionAdjustments);
});
test('the real CPU utility receives exactly the declared capped contextual increment',()=>{
  let checked=0;for(const team of dataset.teams)for(const position of ['QB','WR','TE','DL','LB']){const p=dataset.prospects.find(p=>p.position===position);if(!p)continue;const baseline=draftUtility(game,p,team.id,dataset,models),adjusted=draftUtility(game,p,team.id,dataset,{...models,usagePolicy:policy});assert.ok(Math.abs((adjusted-baseline)-priorUsageAdjustment(game,p,team.id,{...models,usagePolicy:policy}))<1e-12);checked++;}assert.ok(checked>=100);
});
test('historical context changes actual choices while identical seeds remain deterministic',()=>{
  const withContext=autoComplete(game,dataset,{...models,usagePolicy:policy});const again=autoComplete(game,dataset,{...models,usagePolicy:policy});assert.deepEqual(withContext.selections,again.selections);
  const without=autoComplete(game,dataset,models);assert.notDeepEqual(withContext.selections,without.selections);assert.equal(withContext.selections.length,256);
});
test('equal leaderboard scores share competition rank independent of arrival order',()=>{
  const rows=[{name:'third',score:80},{name:'first',score:90},{name:'tied',score:90},{name:'last',score:70},{name:'also-third',score:80}];const original=JSON.stringify(rows);
  assert.deepEqual(rankLeaderboard(rows).map(r=>[r.name,r.rank]),[['first',1],['tied',1],['third',3],['also-third',3],['last',5]]);assert.equal(JSON.stringify(rows),original);assert.throws(()=>rankLeaderboard([{score:NaN}]),/Invalid/);
});
test('scoring calibration rejects malformed seasons and availability cutoffs',()=>{
  const artifact=JSON.parse(readFileSync('analytics/scoring_recalibration.json','utf8'));
  assert.doesNotThrow(()=>validateScoringRecalibration(artifact,cutoff));
  for(const fitThroughSeason of [NaN,Infinity,'2017',2017.5,2018,null,undefined])assert.throws(()=>validateScoringRecalibration({...artifact,fitThroughSeason},cutoff),/cutoff/);
  for(const timestamp of ['invalid','2020-01-01',null,undefined])assert.throws(()=>validateScoringRecalibration({...artifact,cutoff:timestamp},cutoff),/cutoff/);
  assert.throws(()=>validateScoringRecalibration(artifact,'invalid'),/cutoff/);
  for(const meanTotal of [NaN,Infinity,'44',0,-10])assert.throws(()=>validateScoringRecalibration({...artifact,proposedOverride:{meanTotal}},cutoff),/parameters/);
});
