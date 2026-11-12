import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
test('analytical schema:20 current relational, temporal and disclosure constraints',()=>{const r=spawnSync('python3',['tests/warehouse_test.py'],{encoding:'utf8'});assert.equal(r.status,0,r.stdout+r.stderr);assert.match(r.stderr,/Ran 20 tests/);});
