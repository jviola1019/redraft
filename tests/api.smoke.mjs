import {DatabaseSync} from 'node:sqlite';
import {registerHooks,stripTypeScriptTypes} from 'node:module';
import {readFileSync,existsSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';
const root=process.cwd(),sqlite=new DatabaseSync(':memory:');sqlite.exec('PRAGMA foreign_keys=ON');
for(const f of readdirSync('drizzle').filter(f=>f.endsWith('.sql')))sqlite.exec(readFileSync('drizzle/'+f,'utf8'));
let owner='test-user';process.env.NODE_ENV='test';
globalThis.__auth=()=>owner?{userId:owner}:null;
function statement(sql,args=[]){return{bind(...a){return statement(sql,a)},async first(){return sqlite.prepare(sql).get(...args)||null},async all(){return{results:sqlite.prepare(sql).all(...args)}},async run(){const r=sqlite.prepare(sql).run(...args);return{meta:{changes:Number(r.changes)}}}}}
globalThis.__db={prepare:statement,async batch(items){sqlite.exec('BEGIN');try{const r=[];for(const s of items)r.push(await s.run());sqlite.exec('COMMIT');return r}catch(e){sqlite.exec('ROLLBACK');throw e}}};
registerHooks({resolve(spec,ctx,next){if(spec==='cloudflare:workers')return{url:'test:cloudflare',shortCircuit:true};if(spec==='@/app/chatgpt-auth')return{url:'test:auth',shortCircuit:true};let p=spec.startsWith('@/')?resolve(root,spec.slice(2)):spec.startsWith('.')&&ctx.parentURL?.startsWith('file:')?resolve(fileURLToPath(new URL('.',ctx.parentURL)),spec):null;if(p){if(!existsSync(p)){for(const ext of ['.ts','.tsx','.json'])if(existsSync(p+ext)){p+=ext;break}}return next(pathToFileURL(p).href,ctx)}return next(spec,ctx)},load(url,ctx,next){if(url==='test:cloudflare')return{format:'module',source:'export const env={DB:globalThis.__db}',shortCircuit:true};if(url==='test:auth')return{format:'module',source:'export async function getChatGPTUser(){return globalThis.__auth()}',shortCircuit:true};if(url.startsWith('file:')&&url.endsWith('.ts'))return{format:'module',source:stripTypeScriptTypes(readFileSync(fileURLToPath(url),'utf8'),{mode:'transform'}),shortCircuit:true};if(url.endsWith('.json'))return{format:'module',source:'export default '+readFileSync(fileURLToPath(url),'utf8'),shortCircuit:true};return next(url,ctx)}});
const {GET,POST}=await import(pathToFileURL(resolve('app/api/game/route.ts')));
let checks=0;const check=(v)=>{assert.ok(v);checks++};
async function post(body,status=200){const r=await POST(new Request('https://test.local/api/game',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}));const d=await r.json();assert.equal(r.status,status,JSON.stringify(d));checks++;return d}
const create=mode=>post({action:'new',mode,requestId:crypto.randomUUID()},201);
owner=null;check((await GET(new Request('https://test.local/api/game'))).status===401);owner='test-user';
let p=await create('historical');check(p.prospects.length===336);check(p.prospects.every(x=>x.heightIn===null&&x.college==='Hidden until reveal'&&x.id.startsWith('bp_')));
const mutate=async(action,extra={})=>{p=await post({action,id:p.game.id,revision:p.game.revision,requestId:crypto.randomUUID(),...extra});return p};
await mutate('scout',{prospectId:p.prospects[0].id});check(p.prospects.filter(x=>x.scouted).length>=5);
await post({action:'save',id:p.game.id,revision:0,requestId:crypto.randomUUID()},409);
const id=p.game.id;owner='intruder';check((await GET(new Request('https://test.local/api/game?action=load&id='+id))).status===404);owner='test-user';
for(const mode of ['historical','daily']){if(mode==='daily')p=await create(mode);let turns=0;while(p.game.status==='drafting'){check(++turns<100);if(p.game.picks[p.game.selections.length].owner===p.game.team){const used=new Set(p.game.selections.map(s=>s.prospectId));await mutate('pick',{prospectId:p.prospects.find(x=>!used.has(x.id)).id})}else await mutate('advance')}
check(p.game.selections.length===256);check(new Set(p.game.selections.map(s=>s.prospectId)).size===256);
while(p.game.status!=='complete'){sqlite.exec('DELETE FROM rate_windows');await mutate('simulate')}
check(p.game.results.replicates.length===256);check(p.game.identityRevealed===(mode==='historical'));
if(mode==='daily'){check(p.prospects.every(x=>x.college==='Hidden until reveal'));const r=await GET(new Request('https://test.local/api/game?action=leaderboard'));check((await r.json()).leaderboard.length===1)}
const r=await GET(new Request('https://test.local/api/game?action=load&id='+p.game.id));check((await r.json()).game.status==='complete');}
console.log(JSON.stringify({passed:checks,workflows:['historical seven-round draft and256 paired simulations','daily seven-round draft and256 paired simulations','save/reload','group scouting','auth','ownership','stale revisions','identity embargo','leaderboard']}));
