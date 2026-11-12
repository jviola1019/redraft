import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import crypto from 'node:crypto';
import {createRequire} from 'node:module';
import ts from 'typescript';
export const root=path.resolve(import.meta.dirname,'..');
const dir=fs.mkdtempSync(path.join(os.tmpdir(),'redraft-analysis-'));
fs.mkdirSync(path.join(dir,'lib'));
fs.symlinkSync(path.join(root,'analytics'),path.join(dir,'analytics'),'dir');
fs.symlinkSync(path.join(root,'data'),path.join(dir,'data'),'dir');
fs.writeFileSync(path.join(dir,'package.json'),JSON.stringify({type:'commonjs'}));
for(const name of ['types','engine','simulation','scouting','server-data']) {
  fs.writeFileSync(path.join(dir,'lib',name+'.js'),ts.transpileModule(fs.readFileSync(path.join(root,'lib',name+'.ts'),'utf8').replaceAll("'@/", "'"+root+"/"),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,esModuleInterop:true}}).outputText);
}
const require=createRequire(import.meta.url);
export const engine=require(path.join(dir,'lib/engine.js'));
export const sim=require(path.join(dir,'lib/simulation.js'));
// Use exactly the same scenario/model construction as authoritative requests.
const registry=require(path.join(dir,'lib/server-data.js'));
export const {dataset,models,scoutingPolicy}=registry;
export const loadScenario=registry.getScenario;
export const supportedYears=registry.years;
export function cleanup(){fs.rmSync(dir,{recursive:true,force:true});}
export function hashes(){return Object.fromEntries([
  'lib/engine.ts','lib/simulation.ts','lib/scouting.ts','lib/server-data.ts',
  'analytics/model.json','analytics/five_year_strict_2018.json','analytics/scoring_recalibration.json',
  'data/clean/team_context_2018.json','data/clean/team_context_source_manifest.json',
  ...fs.readdirSync(path.join(root,'data/processed')).filter(p=>/^scenario-.*\.json$/.test(p)).map(p=>'data/processed/'+p),
  ...fs.readdirSync(path.join(root,'analytics')).filter(p=>/^model-\d{4}\.json$/.test(p)).map(p=>'analytics/'+p)
].map(p=>[p,crypto.createHash('sha256').update(fs.readFileSync(path.join(root,p))).digest('hex')]));}
export function write(name,data){fs.writeFileSync(path.join(root,'analytics',name),JSON.stringify(data,null,2)+'\n');}
