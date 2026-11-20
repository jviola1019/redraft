#!/usr/bin/env node
/** Descriptive CPU policy backtest; no runtime tuning and no causal quality claim.
 * Run from any cwd: node research/cpu_behavior_audit.mjs --output docs/audit/cpu_behavior_results.json
 */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
// Absolute import is replaced by a relative import only when integrated in research/.
import {root,engine,loadScenario,hashes,cleanup} from '../analytics/runtime_loader.mjs';
const rounds=[1,2,3,4,5,6,7], positions=['QB','RB','WR','TE','OL','DL','LB','DB','K','P','LS'];
const windows={2018:['04-26','04-28'],2019:['04-25','04-27'],2020:['04-23','04-25'],2021:['04-29','05-01'],2022:['04-28','04-30'],2023:['04-27','04-29'],2024:['04-25','04-27'],2025:['04-24','04-26'],2026:['04-23','04-25']};
const repetitions=12;
const mean=a=>a.reduce((s,v)=>s+v,0)/a.length;
const sd=a=>a.length<2?0:Math.sqrt(a.reduce((s,v)=>s+(v-mean(a))**2,0)/(a.length-1));
const rounded=x=>Number(x.toFixed(6));
function summary(a){const b=[...a].sort((x,y)=>x-y);return {mean:rounded(mean(a)),sd:rounded(sd(a)),min:rounded(b[0]),max:rounded(b.at(-1)),monteCarloSe:rounded(sd(a)/Math.sqrt(a.length))};}
function histogram(rows){return Object.fromEntries(positions.map(p=>[p,rows.filter(r=>r.position===p).length]));}
function shares(rows){const h=histogram(rows);return Object.fromEntries(positions.map(p=>[p,rows.length?h[p]/rows.length:0]));}
function tv(a,b){const x=shares(a),y=shares(b);return positions.reduce((s,p)=>s+Math.abs(x[p]-y[p]),0)/2;}
function effective(rows){const p=Object.values(shares(rows)).filter(x=>x>0);return p.length?Math.exp(-p.reduce((s,x)=>s+x*Math.log(x),0)):0;}
// RFC4180-style fields, including embedded commas/quotes/newlines.
function csv(text){const rows=[];let row=[],cell='',quote=false;for(let i=0;i<text.length;i++){const c=text[i];if(c==='"'){if(quote&&text[i+1]==='"'){cell+='"';i++;}else quote=!quote;}else if(c===','&&!quote){row.push(cell);cell='';}else if((c==='\n'||c==='\r')&&!quote){if(c==='\r'&&text[i+1]==='\n')i++;row.push(cell);if(row.some(x=>x!==''))rows.push(row);row=[];cell='';}else cell+=c;}if(cell||row.length){row.push(cell);rows.push(row);}if(quote)throw Error('Unclosed CSV quote');const header=rows.shift();return rows.map(r=>{if(r.length!==header.length)throw Error('CSV column mismatch');return Object.fromEntries(header.map((k,i)=>[k,r[i]]));});}
const rawTrades=csv(fs.readFileSync(path.join(root,'data/raw/trades.csv'),'utf8'));
const latestRecordedTradeDate=rawTrades.map(r=>r.trade_date).sort().at(-1);
function actualTrades(year){const groups=new Map();const [a,b]=windows[year].map(d=>`${year}-${d}`);for(const row of rawTrades){if(row.trade_date<a||row.trade_date>b)continue;if(!groups.has(row.trade_id))groups.set(row.trade_id,[]);groups.get(row.trade_id).push(row);}const transactions=[...groups.values()];const covered=latestRecordedTradeDate>=b;
return {status:covered?'observed-source-extends-past-window':'unavailable-source-ends-before-window',latestRecordedTradeDate,observedDistinctTransactions:transactions.length,distinctTransactions:covered?transactions.length:null,pickRelated:covered?transactions.filter(g=>g.some(r=>r.pick_season)).length:null,currentYearPicksOnly:covered?transactions.filter(g=>g.every(r=>r.pick_season===String(year))).length:null,anyFuturePick:covered?transactions.filter(g=>g.some(r=>Number(r.pick_season)>year)).length:null,withPlayerAsset:covered?transactions.filter(g=>g.some(r=>!r.pick_season)).length:null,windowStart:a,windowEnd:b};}
const sourceHashes=hashes();sourceHashes['data/raw/trades.csv']=crypto.createHash('sha256').update(fs.readFileSync(path.join(root,'data/raw/trades.csv'))).digest('hex');
const classes=[],failures=[];
try{
for(let year=2018;year<=2026;year++){
 const {dataset:d,models:m}=loadScenario(year), byId=new Map(d.prospects.map(p=>[p.id,p]));
 const toRows=rows=>rows.map(s=>({...s,position:engine.positionGroup(byId.get(s.prospectId).position)}));
 const actual=toRows(d.actualPicks), playableActual=actual.filter(s=>engine.isPlayableProspect(byId.get(s.prospectId)));
 const runs=[];const allDrafts=[];
 for(let n=0;n<repetitions;n++){
  const team=d.teams[n%d.teams.length].id,seed=`cpu-policy-audit-${n}`;
  const game=engine.autoComplete(engine.createGame({id:`cpu-audit-${year}-${n}`,year,seed,team,now:'2026-11-20T00:00:00Z'},d),d,m);
  if(game.selections.length!==d.picks.length||new Set(game.selections.map(s=>s.prospectId)).size!==d.picks.length||game.selections.some(s=>!engine.isPlayableProspect(byId.get(s.prospectId))))failures.push(`${year}/${n}: incomplete or ineligible draft`);
  const selections=toRows(game.selections);allDrafts.push(selections);
  runs.push({seed,designatedUserTeam:team,picks:selections.length,trades:game.trades.length,tradesPer100Picks:100*game.trades.length/selections.length,overallPositionTv:tv(selections,actual),firstRoundPositionTv:tv(selections.filter(s=>s.round===1),actual.filter(s=>s.round===1)),franchiseMeanEffectivePositions:mean(d.teams.map(t=>effective(selections.filter(s=>s.team===t.id)))),franchiseMeanActualPositionTv:mean(d.teams.map(t=>tv(selections.filter(s=>s.team===t.id),actual.filter(s=>s.team===t.id)))),firstRoundQb:selections.filter(s=>s.round===1&&s.position==='QB').length,specialists:selections.filter(s=>['K','P','LS'].includes(s.position)).length,selectionSha256:crypto.createHash('sha256').update(JSON.stringify(game.selections)).digest('hex')});
 }
 const byRound=rounds.map(round=>{const a=actual.filter(s=>s.round===round),pa=playableActual.filter(s=>s.round===round),sample=allDrafts.flatMap(s=>s.filter(p=>p.round===round));return {round,actualPicks:a.length,actualPlayablePicks:pa.length,actualPositionCounts:histogram(a),actualPlayablePositionCounts:histogram(pa),cpuMeanPositionCounts:Object.fromEntries(positions.map(p=>[p,rounded(histogram(sample)[p]/repetitions)])),cpuPooledVsActualTv:rounded(tv(sample,a)),cpuPooledVsPlayableActualTv:rounded(tv(sample,pa)),individualRunVsActualTv:summary(allDrafts.map(s=>tv(s.filter(p=>p.round===round),a)))};});
 const byFranchise=d.teams.map(t=>{const a=actual.filter(s=>s.team===t.id);return {team:t.id,actualPicks:a.length,actualReferenceOnly:a.filter(s=>!engine.isPlayableProspect(byId.get(s.prospectId))).length,actualPositions:histogram(a),actualEffectivePositions:rounded(effective(a)),cpuPickCount:summary(allDrafts.map(s=>s.filter(p=>p.team===t.id).length)),cpuEffectivePositions:summary(allDrafts.map(s=>effective(s.filter(p=>p.team===t.id)))),cpuVsActualPositionTv:summary(allDrafts.map(s=>tv(s.filter(p=>p.team===t.id),a)))};});
 const metrics=Object.fromEntries(['trades','tradesPer100Picks','overallPositionTv','firstRoundPositionTv','franchiseMeanEffectivePositions','franchiseMeanActualPositionTv','firstRoundQb','specialists'].map(k=>[k,summary(runs.map(r=>r[k]))]));
 classes.push({year,slots:d.picks.length,playablePool:d.prospects.filter(engine.isPlayableProspect).length,actualReferenceOnly:actual.length-playableActual.length,tradeArrivalRate:m.tradeArrivalRate??.10,actualTrades:actualTrades(year),metrics,actualFirstRoundQb:actual.filter(s=>s.round===1&&s.position==='QB').length,actualSpecialists:actual.filter(s=>['K','P','LS'].includes(s.position)).length,actualMeanEffectivePositions:rounded(mean(byFranchise.map(r=>r.actualEffectivePositions))),byRound,byFranchise,runs});
 console.log(JSON.stringify({year,trades:metrics.trades,actualTrades:actualTrades(year),firstRoundTv:metrics.firstRoundPositionTv.mean,overallTv:metrics.overallPositionTv.mean,qb:[metrics.firstRoundQb.mean,actual.filter(s=>s.round===1&&s.position==='QB').length],specialists:[metrics.specialists.mean,actual.filter(s=>['K','P','LS'].includes(s.position)).length]}));
}
const output={asOf:'2026-11-20',purpose:'Descriptive behavior comparison of frozen production CPU policy against recorded draft outcomes; not a quality, causal or historical-information validation.',repetitionsPerClass:repetitions,totalDrafts:repetitions*classes.length,sourceHashes,definitions:{tv:'Total variation = one half the sum of absolute position-share differences; 0 equal, 1 disjoint. Per-round pooled counts compare average policy shares; individual-run TV also includes sampling noise.',effectivePositions:'exp(Shannon entropy of position shares), per franchise; 1 means single-position class, larger means more diverse. Does not estimate need or quality.',tradeBaseline:'Distinct transactions inside inclusive local draft date windows. Current-year-picks-only excludes player/future-pick assets, matching supported CPU assets more closely. Date-only windows can include off-clock transactions.',monteCarloSe:'Between-seed sample SD / sqrt(12); simulation sampling error only. Not model uncertainty or independent historic sample uncertainty.'},limitations:['12 fixed seeds and 12 rotating designated user franchises per class; auto-completion uses CPU picking for user picks but CPU trades exclude designated user franchise.','No human trades or board decisions; historical all-draftee and playable-only distributions differ because 19–83 actual draftees are reference-only.','Round shares and franchise statistics are descriptive, not a target to tune blindly toward; actual team needs, player quality and opportunity costs are not reconstructed.','Observed trade data need not be exhaustive; source extends only through 2026-04-17, making the 2026 draft trade comparator unavailable. Current-year-only scope misses genuine future-pick/player deals.','No policy tuning, calibration claim, significance test or player-to-wins quality inference is made.'],classes,failures};
const idx=process.argv.indexOf('--output'),out=idx>=0?process.argv[idx+1]:path.join(root,'docs/audit/cpu_behavior_results.json');if(!out)throw Error('--output requires path');fs.writeFileSync(out,JSON.stringify(output,null,2)+'\n');process.exitCode=failures.length?1:0;
}finally{cleanup();}
