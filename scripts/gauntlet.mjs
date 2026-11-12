#!/usr/bin/env node
/** One fixed, auditable QC pass. There is deliberately no retry-until-pass loop. */
import {spawn, spawnSync} from 'node:child_process';
import {createHash, randomUUID} from 'node:crypto';
import {createReadStream, createWriteStream, existsSync, readFileSync, readdirSync, mkdirSync, writeFileSync, copyFileSync, chmodSync, statSync} from 'node:fs';
import {resolve, dirname, relative, join} from 'node:path';
import {fileURLToPath} from 'node:url';
import os from 'node:os';

const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');process.chdir(root);
const args=process.argv.slice(2);
if(args.includes('--help')) {
  console.log('Usage: node scripts/gauntlet.mjs [--label NAME]\nRuns one fixed full QC matrix. Exit 0: executed gates clear; 1: structural/execution/source-drift failure; 2: completed with statistical warnings/failures. A clear run is not full product certification.');process.exit(0);
}
const labelIndex=args.indexOf('--label'),label=labelIndex<0?'audit':args[labelIndex+1];
if(!label||!/^[a-zA-Z0-9_-]{1,50}$/.test(label)||args.some((a,i)=>a!=='--label'&&i!==labelIndex+1))throw Error('Only --label NAME is supported. Labels do not change the fixed seed matrix.');
const startedAt=new Date().toISOString(),runId=`${startedAt.replace(/[:.]/g,'-')}-${label}-${randomUUID().slice(0,8)}`;
const runDir=resolve('tests/results/gauntlet',runId);mkdirSync(runDir,{recursive:true});
function collectFiles() {
const files=new Set();
function addTree(path,accept=()=>true) {if(!existsSync(path))return;for(const item of readdirSync(path,{withFileTypes:true})){const p=join(path,item.name);if(item.isDirectory())addTree(p,accept);else if(item.isFile()&&accept(p))files.add(p);}}
for(const path of ['lib','app','components','db','drizzle'])addTree(path);
for(const path of ['scripts','tests','research','analytics'])addTree(path,p=>/\.(mjs|js|ts|tsx|py|sql)$/.test(p)&&!p.startsWith('tests/results/'));
addTree('data/processed');addTree('data/raw');addTree('docs/warehouse');
for(const path of ['analytics/features','analytics/outcomes'])addTree(path);
for(const path of ['analytics/model.json','analytics/five_year_strict_2018.json','analytics/five_year_research.json','analytics/five_year_strict_labels.csv','analytics/five_year_frozen_2018_predictions.csv','analytics/five_year_retrospective_predictions.csv','analytics/five_year_rolling_predictions.csv','analytics/pooling_validation.json','analytics/coarsening_comparison.json','analytics/scoring_recalibration.json','data/clean/scenario_2018.json','package.json','pnpm-lock.yaml','tsconfig.json'])if(existsSync(path))files.add(path);
addTree('data/clean',p=>/team_context[^/]*\.(json|sha256)$/.test(p));
// Pin directly imported runtime JSON too, so adding a model artifact cannot evade drift checks.
for(const path of [...files].filter(p=>/^(lib|app)\/.+\.(ts|tsx|js|mjs)$/.test(p))) {
  const source=readFileSync(path,'utf8');
  for(const match of source.matchAll(/['"]((?:\.{1,2}\/|@\/)[^'"\n]+\.json)['"]/g)) {
    const absolute=match[1].startsWith('@/')?resolve(match[1].slice(2)):resolve(dirname(path),match[1]);
    if(absolute.startsWith(root+'/')&&existsSync(absolute))files.add(relative(root,absolute));
  }
}
return [...files].sort();
}
async function fileHash(path){const hash=createHash('sha256');for await(const chunk of createReadStream(path))hash.update(chunk);return hash.digest('hex');}
async function snapshot(){const hashes={};for(const p of collectFiles())hashes[p]=await fileHash(p);return hashes;}
const hashJSON=x=>createHash('sha256').update(JSON.stringify(x)).digest('hex');
const initialHashes=await snapshot();
const command=(cmd,argv)=>{const r=spawnSync(cmd,argv,{encoding:'utf8'});return{status:r.status,output:(r.stdout||r.stderr||'').trim()};};
const runtime={node:process.version,python:command('python3',['--version']),platform:os.platform(),architecture:os.arch(),cpu:os.cpus()[0]?.model,logicalCpus:os.cpus().length,memoryBytes:os.totalmem()};
const git={head:command('git',['rev-parse','HEAD']).output,status:command('git',['status','--porcelain']).output};
writeFileSync(join(runDir,'manifest.json'),JSON.stringify({version:'redraft-gauntlet-v1',runId,startedAt,label,runtime,git,sourceHashes:initialHashes,sourceDigest:hashJSON(initialHashes),configuration:{attemptsPerStep:1,leagueMatrix:{teams:32,seeds:3,pairedReplicates:2,replayPerTeam:1},distributionTeams:['CLE','NE','KC','SF'],distributionReplicates:256,scoreSensitivityPolicies:4,scoreSensitivityReplicates:128},limitations:['Command completion does not establish statistical adequacy.','Finite fixed seeds do not exhaust state space.','Runtime measurements are local, not hosted Worker performance.','No browser, WebKit/iPhone or human recognition test is implied.']},null,2)+'\n',{flag:'wx'});

const steps=[],artifacts=[],warnings=[];let activeChild=null,interrupted=false;
for(const signal of ['SIGINT','SIGTERM'])process.on(signal,()=>{interrupted=true;activeChild?.kill('SIGTERM');});
function retain(path,name) {
  if(!existsSync(path))return null;
  const destination=join(runDir,'artifacts',name||path);mkdirSync(dirname(destination),{recursive:true});
  copyFileSync(path,destination,1);artifacts.push(relative(runDir,destination));return destination;
}
async function runStep(id,cmd,argv,{kind='structural',timeoutMs=600000,outputs=[]}={}) {
  if(interrupted)return;
  const began=new Date().toISOString(),time=performance.now(),number=String(steps.length+1).padStart(2,'0');
  const stdoutPath=join(runDir,`${number}-${id}.stdout.log`),stderrPath=join(runDir,`${number}-${id}.stderr.log`);
  const out=createWriteStream(stdoutPath,{flags:'wx'}),err=createWriteStream(stderrPath,{flags:'wx'});
  console.log(`[${number}] ${id} started`);
  let timedOut=false,error=null;
  const exit=await new Promise(done=>{
    const child=spawn(cmd,argv,{cwd:root,env:{...process.env,PYTHONUNBUFFERED:'1'},stdio:['ignore','pipe','pipe']});activeChild=child;
    child.stdout.pipe(out);child.stderr.pipe(err);
    let hardKill=null;
    const timer=setTimeout(()=>{timedOut=true;child.kill('SIGTERM');hardKill=setTimeout(()=>child.kill('SIGKILL'),10000);},timeoutMs);
    child.on('error',e=>{error=String(e);});
    child.on('close',(code,signal)=>{clearTimeout(timer);if(hardKill)clearTimeout(hardKill);activeChild=null;out.end();err.end();done({code,signal});});
  });
  await Promise.all([out.writableFinished?Promise.resolve():new Promise(r=>out.once('finish',r)),err.writableFinished?Promise.resolve():new Promise(r=>err.once('finish',r))]);
  const row={id,kind,command:[cmd,...argv],startedAt:began,finishedAt:new Date().toISOString(),durationMs:performance.now()-time,exitCode:exit.code,signal:exit.signal,timedOut,error,status:exit.code===0&&!timedOut&&!error?'passed':'failed',stdout:relative(runDir,stdoutPath),stderr:relative(runDir,stderrPath),artifacts:[]};
  for(const path of outputs){
    if(existsSync(path)&&statSync(path).mtimeMs>=new Date(began).getTime()-2000) {const dest=retain(path);row.artifacts.push(relative(runDir,dest));}
    else {row.missingFreshArtifact??=[];row.missingFreshArtifact.push(path);row.status='failed';}
  }
  steps.push(row);writeFileSync(join(runDir,`${number}-${id}.result.json`),JSON.stringify(row,null,2)+'\n',{flag:'wx'});
  console.log(`[${number}] ${id}: ${row.status} (${Math.round(row.durationMs)} ms; exit ${exit.code})`);
}

try {
  await runStep('data','python3',['research/test_data.py'],{outputs:['data/clean/order_reconciliation.json','data/clean/eligibility_audit_2018.json']});
  if(existsSync('research/test_team_context.py'))await runStep('team-context','python3',['research/test_team_context.py']);
  await runStep('warehouse','python3',['tests/warehouse_test.py']);
  await runStep('domain',process.execPath,['tests/run.mjs']);
  await runStep('model','python3',['analytics/test_models.py']);
  await runStep('five-year-model','python3',['analytics/five_year_tests.py']);
  if(existsSync('analytics/forecast_audit.py'))await runStep('forecast-audit','python3',['analytics/forecast_audit.py'],{kind:'diagnostic',outputs:['analytics/forecast_audit.json','analytics/forecast_audit_predictions.csv']});
  if(existsSync('analytics/scoring_recalibration.py'))await runStep('scoring-backtest','python3',['analytics/scoring_recalibration.py'],{kind:'diagnostic',outputs:['analytics/scoring_recalibration.json']});
  await runStep('typecheck',process.execPath,['node_modules/typescript/bin/tsc','--noEmit']);
  await runStep('api',process.execPath,['tests/api.integration.mjs'],{outputs:['tests/results/api-integration.json']});
  await runStep('league-matrix',process.execPath,['tests/league-matrix.mjs',join(runDir,'league-matrix.json')]);
  await runStep('all-year-matrix',process.execPath,['tests/all-years.mjs',join(runDir,'all-years')],{timeoutMs:1200000});
  await runStep('playoff-backtest',process.execPath,['tests/playoff-backtest.mjs'],{outputs:['tests/results/playoff-backtest.json']});
  await runStep('all-year-distributions',process.execPath,['analytics/all_year_diagnostics.mjs'],{kind:'diagnostic',outputs:['tests/results/all-year-distributions-2026-11-12.json','tests/results/all-year-distributions-2026-11-12.md']});
  for(const team of ['CLE','NE','KC','SF']) {
    const suffix=team==='CLE'?'':`_${team}`;
    await runStep(`distribution-${team.toLowerCase()}`,process.execPath,['analytics/simulation_diagnostics.mjs','256',team],{kind:'diagnostic',outputs:[`analytics/simulation_diagnostics${suffix}.json`]});
  }
  await runStep('rank-sensitivity-tests',process.execPath,['analytics/test_rank_sensitivity.mjs']);
  await runStep('score-sensitivity',process.execPath,['analytics/score_sensitivity.mjs'],{kind:'diagnostic',outputs:['analytics/score_sensitivity.json']});
  if(existsSync('analytics/test_statistical_gates.py'))await runStep('statistical-integrity-tests','python3',['analytics/test_statistical_gates.py']);
  if(existsSync('analytics/statistical_gates.py'))await runStep('statistical-gates','python3',['analytics/statistical_gates.py'],{kind:'statistical',outputs:['analytics/statistical_gates.json','analytics/STATISTICAL_GATES.md']});
  else warnings.push({kind:'missing-statistical-gates',detail:'Formal statistical gate aggregation is unavailable; forecast validation cannot be reported as passed.'});
} catch(error) {warnings.push({kind:'runner-error',detail:error.stack||String(error)});}

// Read only retained fresh evidence. Previous reports never substitute for failed current commands.
const parsedArtifacts={};
for(const path of artifacts.filter(p=>p.endsWith('.json')))try{parsedArtifacts[path]=JSON.parse(readFileSync(join(runDir,path),'utf8'));}catch(error){warnings.push({kind:'invalid-report',path,detail:String(error)});}
const distributions=Object.entries(parsedArtifacts).filter(([path])=>/simulation_diagnostics(?:_[A-Z]+)?\.json$/.test(path)).map(([path,r])=>({path,team:r.configuration?.team,replicates:r.replicates,distributionFlags:r.distributionFlags,convergence:r.convergence?.at(-1),configuration:r.configuration}));
for(const d of distributions)if(d.distributionFlags?.length)warnings.push({kind:'simulation-distribution',team:d.team,flags:d.distributionFlags});
const allYearDiagnostics=Object.entries(parsedArtifacts).find(([path])=>path.endsWith('/all-year-distributions-2026-11-12.json'));
if(allYearDiagnostics)for(const cohort of allYearDiagnostics[1].classes??[])for(const season of cohort.seasons??[])if(season.adverseFlags?.length)warnings.push({kind:'all-year-distribution',draftYear:cohort.draftYear,season:season.year,flags:season.adverseFlags});
const sensitivity=Object.entries(parsedArtifacts).find(([path])=>path.endsWith('/score_sensitivity.json'));
if(sensitivity&&(sensitivity[1].topRankChanges>0||sensitivity[1].minRankCorrelation===null||sensitivity[1].minRankCorrelation<1))warnings.push({kind:'score-rank-instability',topRankChanges:sensitivity[1].topRankChanges,minRankCorrelation:sensitivity[1].minRankCorrelation,path:sensitivity[0]});
const development=JSON.parse(readFileSync('analytics/five_year_strict_2018.json','utf8'));
if(development.validation?.chronologicallyValidatedFor2018!==true)warnings.push({kind:'strict-2018-calibration-unsupported',detail:development.validation?.reason||'One complete pre-cutoff donor cohort cannot support an internal chronological validation split.'});
const matrixPath=join(runDir,'league-matrix.json');let matrix=null;
try {matrix=JSON.parse(readFileSync(matrixPath,'utf8'));if(matrix.status!=='passed'||matrix.actual.draftCases!==96||matrix.actual.pairedReplicates!==192||matrix.actual.replayPairs!==32)warnings.push({kind:'invalid-report',path:'league-matrix.json',detail:'The entire fixed structural matrix did not pass.'});}
catch(error){warnings.push({kind:'invalid-report',path:'league-matrix.json',detail:String(error)});}
const finalHashes=await snapshot(),drift=[...new Set([...Object.keys(initialHashes),...Object.keys(finalHashes)])].sort().filter(p=>initialHashes[p]!==finalHashes[p]);
const failedStructural=steps.filter(s=>s.status!=='passed'&&(s.kind!=='statistical'||s.exitCode!==2||s.missingFreshArtifact?.length||s.error||s.timedOut)),statisticalStep=steps.find(s=>s.kind==='statistical');
const executionFailed=failedStructural.length>0||drift.length>0||interrupted||warnings.some(w=>['runner-error','invalid-report'].includes(w.kind));
const adverseStatistics=warnings.length>0||statisticalStep?.status==='failed';
const exitCode=executionFailed?1:adverseStatistics?2:0;
const coverage={expectedSteps:18+(existsSync('research/test_team_context.py')?1:0)+(existsSync('analytics/forecast_audit.py')?1:0)+(existsSync('analytics/scoring_recalibration.py')?1:0)+(existsSync('analytics/test_statistical_gates.py')?1:0),completedSteps:steps.length,finiteMatrix:'All registered classes: 32 teams × 3 draft seeds × 2 paired replicates, plus one deterministic replay per team; separate default-class matrix retained',productionBrowser:'not run',humanRecognitionStudy:'not run',publicLoadAndAbuseTest:'not run'};
const report={version:'redraft-gauntlet-v1',runId,startedAt,finishedAt:new Date().toISOString(),runtime,git,steps,sourceDigestBefore:hashJSON(initialHashes),sourceDigestAfter:hashJSON(finalHashes),sourceDrift:drift,finalHashes,artifacts,coverage,matrix:matrix?{status:matrix.status,actual:matrix.actual}:null,distributions,scoreSensitivity:sensitivity?{artifact:sensitivity[0],topRankChanges:sensitivity[1].topRankChanges,minRankCorrelation:sensitivity[1].minRankCorrelation}:null,warnings,structuralStatus:executionFailed?'failed':'passed',statisticalStatus:adverseStatistics?'not-passed':'no-adverse-implemented-checks',releaseStatus:'research-alpha; this runner does not certify all acceptance criteria',interrupted,exitCode};
writeFileSync(join(runDir,'report.json'),JSON.stringify(report,null,2)+'\n',{flag:'wx'});
const lines=[`# REDRAFT QC run ${runId}`,'',`Executed ${startedAt} through ${report.finishedAt}. Source commit: ${git.head}.`,'',`Structural/execution status: **${report.structuralStatus}**. Statistical status: **${report.statisticalStatus}**. Exit code: **${exitCode}**.`,'','| Step | Type | Result | Seconds | Log |','|---|---|---|---:|---|',...steps.map(s=>`| ${s.id} | ${s.kind} | ${s.status} | ${(s.durationMs/1000).toFixed(2)} | [stdout](${s.stdout}) · [stderr](${s.stderr}) |`),'',`Source changes during run: ${drift.length?drift.join(', '):'none detected in the recorded input set'}.`,'',`Warnings retained: ${warnings.length}. Inspect [machine-readable report](report.json), [manifest](manifest.json) and [all-team structural matrix](league-matrix.json).`,'','This fixed finite audit covers implementation behavior. It does not establish causal counterfactual accuracy, complete historical reconstruction, human recognition resistance, WebKit/iPhone behavior or production load limits. Statistical distribution flags and score instability remain adverse evidence when unit tests pass. No failed seed is replaced and every step runs at most once.',''];
writeFileSync(join(runDir,'REPORT.md'),lines.join('\n'),{flag:'wx'});
// Evidence directories are append-only by convention; files are write-protected after completion.
function seal(path){for(const item of readdirSync(path,{withFileTypes:true})){const p=join(path,item.name);if(item.isDirectory())seal(p);else chmodSync(p,0o444);}}
seal(runDir);
console.log('GAUNTLET_REPORT',JSON.stringify({run:relative(root,runDir),structural:report.structuralStatus,statistical:report.statisticalStatus,sourceDrift:drift.length,exitCode}));
process.exitCode=exitCode;
