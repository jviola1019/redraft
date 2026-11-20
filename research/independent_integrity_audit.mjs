#!/usr/bin/env node
/** Independent black-box history/eligibility audit; no generated training labels are trusted.
 * Run: node research/independent_integrity_audit.mjs
 * Uses the runtime registry loader only to exercise the authoritative model bundles.
 */
import fs from 'node:fs';
import crypto from 'node:crypto';
import {root, engine, loadScenario, cleanup, hashes} from '../analytics/runtime_loader.mjs';
const fields = ['heightIn','weightLb','forty','bench','verticalIn','broadJumpIn','cone','shuttle'];
const read = p => JSON.parse(fs.readFileSync(`${root}/${p}`, 'utf8'));
const digest = value => crypto.createHash('sha256').update(JSON.stringify(value)).digest('hex');
const failures = [], records = [];
function check(ok, message) { if (!ok) failures.push(message); }
const snapshot = hashes();
for (const path of ['research/independent_integrity_audit.mjs','analytics/train_models.py','analytics/project_scenarios.py','analytics/features/combine_model_features.csv','analytics/outcomes/rookie_snap_labels.csv']) {
  snapshot[path]=crypto.createHash('sha256').update(fs.readFileSync(`${root}/${path}`)).digest('hex');
}
// These two generated CSVs have no quoted/comma-containing cells. Fail if that
// assumption changes rather than silently mis-parsing an expanded schema.
function csv(path) {
  const text=fs.readFileSync(`${root}/${path}`,'utf8').trim();
  if(text.includes('"')) throw new Error(`CSV parser requires unquoted cells: ${path}`);
  const [header,...lines]=text.split(/\r?\n/), columns=header.split(',');
  return lines.map(line=>{const cells=line.split(',');if(cells.length!==columns.length)throw new Error(`CSV width mismatch: ${path}`);return Object.fromEntries(columns.map((k,i)=>[k,cells[i]]));});
}
const trainingFeatures=csv('analytics/features/combine_model_features.csv');
const trainingLabels=csv('analytics/outcomes/rookie_snap_labels.csv');
const key=r=>`${r.season}:${r.pfr_id}`;
check(trainingFeatures.length===trainingLabels.length && new Set(trainingFeatures.map(key)).size===trainingFeatures.length && new Set(trainingLabels.map(key)).size===trainingLabels.length, 'Training identity/label row uniqueness mismatch');
const labelKeys=new Set(trainingLabels.map(key));
check(trainingFeatures.every(r=>labelKeys.has(key(r))), 'Training feature/label IDs differ');
check(trainingFeatures.every(r=>Number(r.season)>=2013&&Number(r.season)<=2017), 'Training feature cohort outside 2013–17');
check(trainingLabels.every(r=>Number(r.season)>=2013&&Number(r.season)<=2017&&Number.isFinite(Date.parse(r.label_available_by))&&Date.parse(r.label_available_by)<=Date.parse('2018-04-26T00:00:00Z')&&Number(r.y)===(Number(r.snaps)>=200?1:0)), 'Training label timing/target violation');
const trainingAudit={rows:trainingFeatures.length,cohorts:[...new Set(trainingFeatures.map(r=>Number(r.season)))],latestDeclaredLabelAvailability:trainingLabels.map(r=>r.label_available_by).sort().at(-1),archivalFeatureTimestamps:trainingFeatures.filter(r=>r.original_available_at).length};
try {
  for (let year = 2018; year <= 2026; year++) {
    const {dataset:d, models:m, scoutingPolicy, teamContextMetadata} = loadScenario(year);
    const cut = Date.parse(d.metadata.informationCutoff);
    const playable = d.prospects.filter(p => p.eligibilitySource === 'combine-participant');
    const ids = new Set(d.prospects.map(p => p.id));
    const playableIds = new Set(playable.map(p => p.id));
    const actualIds = new Set(d.actualPicks.map(p => p.prospectId));
    check(ids.size === d.prospects.length, `${year}: duplicate prospect IDs`);
    check(d.teams.length === 32 && new Set(d.teams.map(t => t.id)).size === 32, `${year}: invalid teams`);
    check(playable.length >= d.picks.length, `${year}: insufficient playable pool`);
    check(playable.length === d.metadata.playableProspectCount, `${year}: playable metadata differs`);
    check(d.actualPicks.length === d.picks.length && actualIds.size === d.actualPicks.length && [...actualIds].every(id => ids.has(id)), `${year}: invalid baseline references`);
    check(d.picks.map(p=>p.overall).sort((a,b)=>a-b).every((n,i)=>n===i+1), `${year}: duplicate/missing pick slots`);
    const late = playable.filter(p => !Number.isFinite(Date.parse(p.availableBy)) || Date.parse(p.availableBy)>cut);
    check(!late.length, `${year}: invalid/late declared feature availability`);
    const suspicious = d.prospects.flatMap(p => Object.keys(p).filter(k => /draft.?pick|draft.?round|career|rookie|outcome|wins|starts|snap|av$|all.?pro|pro.?bowl/i.test(k)).map(k => `${p.id}:${k}`));
    check(!suspicious.length, `${year}: retrospective prospect field: ${suspicious.slice(0,3)}`);
    const projections = m.prospect.projections;
    check(playable.every(p => projections.some(q=>q.prospectId===p.id)), `${year}: missing playable projection`);
    check(scoutingPolicy.audit.minimumGroupSize>=5, `${year}: blind profile under five`);
    const artifact = read(year===2018 ? 'analytics/model.json' : `analytics/model-${year}.json`);
    const fitThrough = year===2018 ? artifact.team.fitThroughSeason : artifact.fitThroughSeason;
    check(fitThrough<year, `${year}: future training season`);
    const clone = structuredClone(d);
    clone.actualPicks.reverse();
    clone.actualPicks.forEach((p,i)=>{p.team=d.teams[i%32].id;});
    clone.games.forEach(g=>{if(g.season>=year){g.homeScore=999;g.awayScore=0;}});
    // Poison fields commonly implicated in draft-model leakage. These are intentionally
    // absent from the real prospect schema and must not influence runtime selection.
    clone.prospects.forEach((p,i)=>Object.assign(p,{draftPick:i+1,draftRound:1,careerAv:1e8-i,rookieSnaps:1e7-i}));
    const runs=[];
    for (const seed of ['integrity-a','integrity-b']) {
      const config={id:`audit-${year}-${seed}`,year,team:'NE',seed,now:'2026-11-20T00:00:00Z'};
      const normal=engine.autoComplete(engine.createGame(config,d),d,m);
      const poisoned=engine.autoComplete(engine.createGame(config,clone),clone,m);
      const signature = g=>digest({selections:g.selections,trades:g.trades});
      check(signature(normal)===signature(poisoned), `${year}/${seed}: retrospective-history poison changed draft`);
      check(normal.selections.length===d.picks.length && normal.selections.every(s=>playableIds.has(s.prospectId)), `${year}/${seed}: ineligible/incomplete draft`);
      runs.push({seed,selections:normal.selections.length,trades:normal.trades.length,signature:signature(normal),poisonInvariant:signature(normal)===signature(poisoned)});
    }
    records.push({year,cutoff:d.metadata.informationCutoff,playable:playable.length,referenceOnly:d.prospects.length-playable.length,picks:d.picks.length,actualDrafteesPlayable:[...actualIds].filter(id=>playableIds.has(id)).length,allMeasurementsMissing:playable.filter(p=>fields.every(k=>p[k]===null||p[k]===undefined)).length,measurementMissingCells:playable.reduce((n,p)=>n+fields.filter(k=>p[k]===null||p[k]===undefined).length,0),lateAvailability:late.length,fitThrough,minimumBlindGroup:scoutingPolicy.audit.minimumGroupSize,contextAvailable:teamContextMetadata.available,observedRegularGames:Array.from({length:5},(_,i)=>({season:year+i,count:d.games.filter(g=>g.season===year+i&&g.type==='REG').length})),orderWarning:d.metadata.orderWarning,cutoffConfidence:d.metadata.informationCutoffConfidence,runs});
  }
  const output={trainingAudit,audit:'Independent eligibility, declared availability, coverage and history-poisoning audit',asOf:'2026-11-20',scope:'Local artifacts; 2 deterministic complete drafts per class. No network or archival-source verification.',sourceHashes:snapshot,classes:records,failures};
  fs.writeFileSync(`${root}/docs/audit/data_integrity_results.json`,JSON.stringify(output,null,2)+'\n');
  console.log(JSON.stringify({classes:records.map(({year,playable,referenceOnly,picks,actualDrafteesPlayable,allMeasurementsMissing,measurementMissingCells,lateAvailability,contextAvailable})=>({year,playable,referenceOnly,picks,actualDrafteesPlayable,allMeasurementsMissing,measurementMissingCells,lateAvailability,contextAvailable})),fullDraftComparisons:records.length*2,failures},null,2));
  process.exitCode=failures.length?1:0;
} finally { cleanup(); }
