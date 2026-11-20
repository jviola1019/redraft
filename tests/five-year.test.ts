import test from 'node:test';
import assert from 'node:assert/strict';
import model from '../analytics/five_year_strict_2018.json';
import {readFileSync} from 'node:fs';
import {autoComplete,createGame} from '../lib/engine';
import {simulateReplicate,donorSeasonExposure} from '../lib/simulation';
import type {Dataset} from '../lib/types';
test('five-year donor labels end before historical cutoff',()=>{assert.deepEqual(model.cohorts,[2013]);assert.deepEqual(model.labelSeasons,[2013,2017]);assert.equal(model.validation.chronologicallyValidatedFor2018,false);assert.ok(new Date('2018-03-01')<new Date(model.cutoff));});
test('five-year vectors preserve missingness exclusions and valid joint outcomes',()=>{assert.equal(model.donors.length,310);for(const d of model.donors){assert.equal(d.snaps.length,5);assert.equal(d.games.length,5);assert.equal(d.rookieRole,d.snaps[0]>=200);for(let i=0;i<5;i++){assert.ok(Number.isInteger(d.games[i])&&d.games[i]>=0&&d.games[i]<=17);assert.ok(Number.isFinite(d.snaps[i])&&d.snaps[i]>=0);if(d.games[i]===0)assert.equal(d.snaps[i],0);}}});
test('empirical five-year simulation is reproducible and supports zero participation',()=>{const data=JSON.parse(readFileSync('data/processed/scenario-2018.json','utf8')) as Dataset;const g=autoComplete(createGame({seed:'empirical-fiveyear',team:'CLE'},data),data);const a=simulateReplicate(g,0,data);assert.deepEqual(a,simulateReplicate(g,0,data));assert.ok(a.alternate.seasons.flatMap(s=>s.players).some(p=>p.games===0));assert.notDeepEqual(a,simulateReplicate(g,1,data));});

test('donor exposure preserves 16-game seasons and scales 17-game participation',()=>{
    assert.deepEqual(donorSeasonExposure(800,16,2020),{snaps:800,games:16});
    assert.deepEqual(donorSeasonExposure(800,16,2021),{snaps:850,games:17});
    assert.deepEqual(donorSeasonExposure(400,8,2022),{snaps:425,games:9});
    assert.deepEqual(donorSeasonExposure(0,0,2026),{snaps:0,games:0});
    for(const d of model.donors)for(let age=0;age<5;age++){
        const projected=donorSeasonExposure(d.snaps[age],d.games[age],2021);
        assert.equal(projected.snaps/(800*17/16),d.snaps[age]/800);
        assert.ok(Number.isInteger(projected.games)&&projected.games<=17);
    }
});
