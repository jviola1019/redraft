import test from 'node:test';
import assert from 'node:assert/strict';
import {matrixSeeds, validateMatrixReceipt, validateReleaseYears} from './matrix-receipt.mjs';

// Synthetic fixtures exercise report validation only. No simulated or historical claims.
const teams = Array.from({length:32}, (_, i) => 'FixtureTeam' + i);
const expected = {year:2018, teams, datasetVersion:'fixture-data', engineVersion:'fixture-engine', modelVersion:'fixture-model'};
function receipt() {
  return {status:'passed', errors:[], failures:[], sourceChanged:false, sourceHashes:{engine:'a'.repeat(64)}, finalHashes:{engine:'a'.repeat(64)},
    configuration:{...expected, scenarioYear:2018,seeds:matrixSeeds,pairedReplicatesPerCase:2},
    actual:{draftCases:96,passedCases:96,failedCases:0,pairedReplicates:192,replayPairs:32,worlds:384,seasons:1920},
    rows:teams.flatMap(team => matrixSeeds.map((seed:string) => ({team,seed,status:'passed',draftHash:'d'.repeat(64),replay:seed===matrixSeeds[0],
      replicates:[0,1].map(index=>({index,hash:'e'.repeat(64),worldHash:String(index).repeat(64)}))})))};
}
test('accept a complete fixture matrix and reject invalid details even with passing counters', () => {
  validateMatrixReceipt(receipt(), expected);
  const corruptions: ((r:ReturnType<typeof receipt>) => void)[] = [
    r=>{r.rows=[]}, r=>{r.rows[1]=r.rows[0]}, r=>{r.configuration.scenarioYear++},
    r=>{r.rows[1].replicates[0].index=1}, r=>{r.rows[1].replicates[0].worldHash=''},
    r=>{r.rows[1].replay=true}, r=>{r.configuration.modelVersion='old'},
    r=>{r.finalHashes.engine='b'.repeat(64)}
  ];
  for (const corrupt of corruptions) {const r=receipt(); corrupt(r); assert.throws(()=>validateMatrixReceipt(r,expected));}
});
test('reject empty, missing and duplicate release class fixtures', () => {
  const years=Array.from({length:9},(_,i)=>2018+i);
  validateReleaseYears(years);
  for (const invalid of [[], years.slice(1), [...years,2026]]) assert.throws(()=>validateReleaseYears(invalid));
});
