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
for(const name of ['types','engine','simulation','scouting']) {
  fs.writeFileSync(path.join(dir,'lib',name+'.js'),ts.transpileModule(fs.readFileSync(path.join(root,'lib',name+'.ts'),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,esModuleInterop:true}}).outputText);
}
const require=createRequire(import.meta.url);
export const engine=require(path.join(dir,'lib/engine.js'));
export const sim=require(path.join(dir,'lib/simulation.js'));
export const dataset=JSON.parse(fs.readFileSync(path.join(root,'data/processed/scenario-2018.json'),'utf8'));
const baseModels=JSON.parse(fs.readFileSync(path.join(root,'analytics/model.json'),'utf8'));
export const scoutingPolicy=require(path.join(dir,'lib/scouting.js')).createScoutingPolicy(dataset,baseModels);
const contextBytes=fs.readFileSync(path.join(root,'data/clean/team_context_2018.json'));
const context=JSON.parse(contextBytes.toString('utf8'));
const manifest=JSON.parse(fs.readFileSync(path.join(root,'data/clean/team_context_source_manifest.json'),'utf8'));
const contextHash=crypto.createHash('sha256').update(contextBytes).digest('hex');
if(contextHash!==manifest.artifactSha256) throw new Error('Team context provenance hash mismatch.');
const usagePolicy=engine.createUsagePolicy(context,String(dataset.metadata.informationCutoff),manifest.artifactSha256);
const scoring=JSON.parse(fs.readFileSync(path.join(root,'analytics/scoring_recalibration.json'),'utf8'));
export const models={...scoutingPolicy.pooledModels,usagePolicy,
  team:{...scoutingPolicy.pooledModels.team,meanTotal:scoring.proposedOverride.meanTotal},
  version:`${scoutingPolicy.pooledModels.version}+five-year-2013-v1+${usagePolicy.version}:${usagePolicy.sourceSha256.slice(0,12)}+scoring-trailing3-v1`};
export function cleanup(){fs.rmSync(dir,{recursive:true,force:true});}
export function hashes(){return Object.fromEntries([
  'lib/engine.ts','lib/simulation.ts','lib/scouting.ts','lib/server-data.ts',
  'analytics/model.json','analytics/five_year_strict_2018.json','analytics/scoring_recalibration.json',
  'data/processed/scenario-2018.json','data/clean/team_context_2018.json','data/clean/team_context_source_manifest.json'
].map(p=>[p,crypto.createHash('sha256').update(fs.readFileSync(path.join(root,p))).digest('hex')]));}
export function write(name,data){fs.writeFileSync(path.join(root,'analytics',name),JSON.stringify(data,null,2)+'\n');}
