#!/usr/bin/env node
import fs from 'node:fs';
import crypto from 'node:crypto';
import {root,engine,loadScenario,cleanup} from '../../../analytics/runtime_loader.mjs';
const candidate=JSON.parse(fs.readFileSync('/tmp/cpu_candidate_paired.json','utf8'));
const original=JSON.parse(fs.readFileSync(new URL('../cpu_behavior_results.json',import.meta.url),'utf8'));
const rerun=JSON.parse(fs.readFileSync('/tmp/cpu_current_paired.json','utf8'));
const signature=g=>crypto.createHash('sha256').update(JSON.stringify(g.selections)).digest('hex');
const failures=[],runs=[];
try{
for(const c of rerun.classes){const previous=original.classes.find(x=>x.year===c.year);for(let i=0;i<c.runs.length;i++){if(c.runs[i].selectionSha256!==previous.runs[i].selectionSha256)failures.push(`Baseline replay mismatch ${c.year}/${i}`);}}
for(let year=2018;year<=2026;year++){
 const {dataset:d,models:m}=loadScenario(year);m.positionRoundPrior=candidate.priorFit.positionRoundPrior;
 for(let n=0;n<2;n++){
  const cfg={id:`candidate-invariants-${year}-${n}`,year,seed:`cpu-policy-audit-${n}`,team:d.teams[n].id,now:'2026-11-20T00:00:00Z'};
  const normal=engine.autoComplete(engine.createGame(cfg,d),d,m);
  const poisoned=structuredClone(d);poisoned.actualPicks.reverse();poisoned.actualPicks.forEach((p,i)=>p.team=d.teams[i%32].id);poisoned.games.forEach(g=>{if(g.season>=year){g.homeScore=999;g.awayScore=0;}});poisoned.prospects.forEach((p,i)=>Object.assign(p,{draftPick:i+1,draftRound:1,careerAv:1e8-i,rookieSnaps:1e7-i}));
  const alternate=engine.autoComplete(engine.createGame(cfg,poisoned),poisoned,m);
  const expected=candidate.classes.find(x=>x.year===year).runs[n].selectionSha256;
  const record={year,seed:cfg.seed,replayEqual:signature(normal)===expected,historyPoisonEqual:signature(normal)===signature(alternate),tradePoisonEqual:JSON.stringify(normal.trades)===JSON.stringify(alternate.trades)};
  if(!record.replayEqual||!record.historyPoisonEqual||!record.tradePoisonEqual)failures.push(`${year}/${n}: noninterference/replay failed`);
  runs.push(record);
 }
}
const result={baselineReplays:108,candidateReplays:18,pairedPoisonChecks:18,candidateFitRows:candidate.priorFit.rows,candidateFitCohorts:candidate.priorFit.cohorts,runs,failures};fs.writeFileSync('/tmp/cpu_candidate_invariants.json',JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));process.exitCode=failures.length?1:0;
}finally{cleanup();}
