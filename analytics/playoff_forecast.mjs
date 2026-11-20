import fs from 'node:fs';
import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
import {engine,sim,loadScenario,cleanup,hashes,root} from './runtime_loader.mjs';
const protocol=JSON.parse(fs.readFileSync(new URL('./playoff_forecast_protocol.json',import.meta.url)));
export function qualificationLabels(dataset,year,maxYear=2025){
 if(year>maxYear||!sim.actualSeasonIsComplete(dataset,year))return null;
 const eligible=new Set(dataset.teams.map(t=>t.id));
 const qualifiers=new Set(dataset.games.filter(g=>g.season===year&&g.type!=='REG').flatMap(g=>[g.home,g.away]));
 assert.equal(qualifiers.size,year<2020?12:14);
 assert.ok([...qualifiers].every(t=>eligible.has(t)));
 return Object.fromEntries(dataset.teams.map(t=>[t.id,Number(qualifiers.has(t.id))]));
}
function summarize(rows){
 const mean=a=>a.reduce((s,x)=>s+x,0)/a.length;
 const brier=mean(rows.map(r=>(r.probability-r.actual)**2));
 const reference=mean(rows.map(r=>(r.slotPrevalence-r.actual)**2));
 const bias=mean(rows.map(r=>r.probability*(1-r.probability)/(protocol.replicatesPerOrigin-1)));
 // Delta-method MC variance: independent seed replicates within each origin,
 // preserving dependence among teams and across horizons within each path.
 let variance=0;
 for(const origin of [...new Set(rows.map(r=>r.origin))]){
  const rr=rows.filter(r=>r.origin===origin),n=protocol.replicatesPerOrigin;
  const influence=Array.from({length:n},(_,i)=>rr.reduce((v,r)=>v+2*(r.probability-r.actual)*(r.draws[i]-r.probability),0)/rows.length);
  const avg=mean(influence);variance+=influence.reduce((s,v)=>s+(v-avg)**2,0)/(n*(n-1));
 }
 return {rows:rows.length,distinctActualTeamSeasons:new Set(rows.map(r=>r.year+'-'+r.team)).size,brier,prevalenceBrier:reference,brierSkill:1-brier/reference,estimatedFiniteSeedBrierBias:bias,biasAdjustedBrier:brier-bias,deltaMethodMonteCarloSE:Math.sqrt(variance),meanPredicted:mean(rows.map(r=>r.probability)),observedPrevalence:mean(rows.map(r=>r.actual))};
}
export function validateRows(rows){
 for(const r of rows){assert.ok(r.year<=2025);assert.ok(r.horizon>=1&&r.horizon<=5);assert.equal(r.year,r.origin+r.horizon-1);assert.ok(r.probability>=0&&r.probability<=1);assert.ok([0,1].includes(r.actual));assert.equal(r.draws.length,protocol.replicatesPerOrigin);assert.ok(r.draws.every(x=>x===0||x===1));}
 for(const key of new Set(rows.map(r=>r.origin+'-'+r.year))){const g=rows.filter(r=>r.origin+'-'+r.year===key);assert.equal(g.length,32);assert.equal(new Set(g.map(r=>r.team)).size,32);const slots=g[0].year<2020?12:14;assert.equal(g.reduce((s,r)=>s+r.actual,0),slots);assert.ok(Math.abs(g.reduce((s,r)=>s+r.probability,0)-slots)<1e-9);}
 return true;
}
export async function run(){
 const start=performance.now(),rows=[],excluded=[],origins=[];
 // Labels pool is read once, held separate from simulation features.
 const observed=new Map();
 for(const origin of protocol.origins)for(const g of loadScenario(origin).dataset.games){if(observed.has(g.id))assert.deepEqual(observed.get(g.id),g);else observed.set(g.id,g);}
 for(const origin of protocol.origins){
  const {dataset,models}=loadScenario(origin);const labelsDataset={...dataset,games:[...observed.values()]};
  let game=engine.createGame({team:'CLE',seed:protocol.seed+'|origin|'+origin,now:`${origin}-04-01T00:00:00Z`,modelVersion:models.version},dataset);
  // Alternate draft exists solely to satisfy the public API's complete-game
  // validation. Only baseline (actual recorded draft, zero trades) is scored.
  game=engine.autoComplete(game,dataset,models);
  const groups=new Map();
  for(let h=1;h<=5;h++){
   const year=origin+h-1,labels=qualificationLabels(labelsDataset,year);
   if(!labels){excluded.push({origin,year,horizon:h,reason:year>2025?'after completed-year cutoff':'incomplete actual season'});continue;}
   for(const team of dataset.teams){const r={origin,year,horizon:h,team:team.id,actual:labels[team.id],slotPrevalence:(year<2020?12:14)/32,draws:[]};rows.push(r);groups.set(year+'-'+team.id,r);}
  }
  for(let i=0;i<protocol.replicatesPerOrigin;i++){
   const baseline=sim.simulateReplicate(game,i,dataset,models).baseline;
   for(const season of baseline.seasons)for(const team of season.teams){const r=groups.get(season.year+'-'+team.team);if(r)r.draws.push(Number(team.playoff));}
  }
  origins.push({origin,modelVersion:models.version,fitThroughSeason:models.team.fitThroughSeason??null,scoredTeamSeasons:groups.size});
  console.log(`origin ${origin}: ${groups.size} team-season forecasts`);
 }
 for(const r of rows)r.probability=r.draws.reduce((a,b)=>a+b,0)/r.draws.length;
 validateRows(rows);
 const result={protocol,sourceHashes:hashes(),origins,excluded,overall:summarize(rows),byOrigin:Object.fromEntries(protocol.origins.map(o=>[o,summarize(rows.filter(r=>r.origin===o))])),byHorizon:Object.fromEntries([1,2,3,4,5].map(h=>[h,summarize(rows.filter(r=>r.horizon===h))])),byActualYear:Object.fromEntries(protocol.origins.map(y=>[y,summarize(rows.filter(r=>r.year===y))])),runtimeMilliseconds:performance.now()-start,rows};
 fs.writeFileSync(root+'/analytics/playoff_forecast_results.json',JSON.stringify(result,null,2)+'\n');
 cleanup();console.log(JSON.stringify({overall:result.overall,byHorizon:result.byHorizon,runtimeMilliseconds:result.runtimeMilliseconds},null,2));
 return result;
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href)await run();
