import assert from 'node:assert/strict';
import fs from 'node:fs';
import {qualificationLabels,validateRows} from './playoff_forecast.mjs';
import {engine,sim,loadScenario,cleanup,root} from './runtime_loader.mjs';
const checks=[];
try{
 for(let year=2018;year<=2025;year++){
  const {dataset,models}=loadScenario(year);
  const labels=qualificationLabels(dataset,year);assert.ok(labels,`complete ${year}`);
  const post=dataset.games.filter(g=>g.season===year&&g.type!=='REG');
  const wc=new Set(post.filter(g=>g.type==='WC').flatMap(g=>[g.home,g.away]));
  const byes=[...new Set(post.flatMap(g=>[g.home,g.away]))].filter(t=>!wc.has(t));
  assert.equal(byes.length,year<2020?4:2);for(const team of byes)assert.equal(labels[team],1);
  assert.equal(Object.values(labels).reduce((a,b)=>a+b,0),year<2020?12:14);
  const index=dataset.games.findIndex(g=>g.season===year&&g.type==='REG');
  const missing={...dataset,games:dataset.games.filter((_,i)=>i!==index)};
  assert.equal(qualificationLabels(missing,year),null);
  let game=engine.createGame({team:'CLE',seed:'forecast-score-poisoning|'+year,now:`${year}-04-01T00:00:00Z`,modelVersion:models.version},dataset);
  game=engine.autoComplete(game,dataset,models);
  const poisoned={...dataset,games:dataset.games.map(g=>g.season>=year?{...g,homeScore:999,awayScore:998}:g)};
  assert.deepEqual(sim.simulateReplicate(game,0,dataset,models).baseline,sim.simulateReplicate(game,0,poisoned,models).baseline,`Future outcome poison changes ${year} baseline`);
 }
 checks.push('All 2018–2025 labels include postseason bye teams and exact qualification slot counts');
 checks.push('Removing one regular-season actual game excludes each incomplete year');
 const {dataset}=loadScenario(2025);assert.equal(qualificationLabels(dataset,2026),null);assert.equal(qualificationLabels(dataset,2027),null);
 checks.push('2026 incomplete and 2027 future actuals excluded');
 checks.push('Poisoning every origin-and-later recorded score leaves seed-0 baseline unchanged at all eight origins');
 const result=JSON.parse(fs.readFileSync(root+'/analytics/playoff_forecast_results.json'));
 assert.equal(result.rows.length,960);assert.equal(result.overall.distinctActualTeamSeasons,256);validateRows(result.rows);
 for(let origin=2018;origin<=2025;origin++)assert.equal(result.rows.filter(r=>r.origin===origin).length,32*Math.min(5,2026-origin));
 checks.push('960 complete all-franchise forecasts, 256 distinct actual team-seasons; valid probability bounds and exact 64 draws each');
 fs.writeFileSync(root+'/analytics/playoff_forecast_tests.json',JSON.stringify({passed:true,checks},null,2)+'\n');console.log(checks.join('\n'));
}finally{cleanup();}
