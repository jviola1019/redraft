import { env } from 'cloudflare:workers';
import { z } from 'zod';
import { getChatGPTUser } from '@/app/chatgpt-auth';
import { dataset, models, scoutingPolicy, teamContexts, teamContextMetadata, selectedTeamContext, getScenario, years, coverage } from '@/lib/server-data';
import { createGame, advance, scout, select, setBoard, proposeTrade, applyTrade, validateGame, random, rankLeaderboard, RULE_VERSION, SCORING_VERSION, ENSEMBLE_SIZE } from '@/lib/engine';
import { simulateReplicate, compactReplicate, summarizeResults } from '@/lib/simulation';
import { aliasCatalog, prospectViews, identityRevealed, BLIND_POLICY_VERSION, type AliasCatalog } from '@/lib/scouting';
import type { GameState } from '@/lib/types';

export const dynamic = 'force-dynamic';
type StoredGame = GameState & { blindSalt: string; scoutingVersion: string };
type RunRow = { id:string; owner:string; challenge_date:string|null; state:string; revision:number };
type DailyConfig = { date:string; team:string; year:number; seed:string; blindSalt:string; modelVersion:string; datasetVersion:string; engineVersion:string; scoringVersion:string; scoutingVersion:string; ensembleSize:number };
class HttpError extends Error { constructor(public status:number,message:string){super(message)} }
const json = (body:unknown,status=200) => Response.json(body,{status,headers:{'Cache-Control':'private, no-store','X-Content-Type-Options':'nosniff'}});
const utcDate = () => new Date().toISOString().slice(0,10);
const token = () => crypto.randomUUID()+crypto.randomUUID();
const hash = async (value:string) => Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(value))),v=>v.toString(16).padStart(2,'0')).join('');
const alias = async (owner:string) => `GM-${(await hash(owner)).slice(0,6).toUpperCase()}`;
function db(){if(!env.DB)throw new HttpError(503,'Saved games are temporarily unavailable.');return env.DB;}
async function identity(){const user=await getChatGPTUser();if(user)return user.userId;if(process.env.NODE_ENV==='development'&&process.env.REDRAFT_LOCAL_IDENTITY==='1')return 'local-development-fixture';throw new HttpError(401,'Sign in with ChatGPT to save your draft.');}
function failure(error:unknown){
  if(error instanceof HttpError)return json({error:error.message},error.status);
  if(error instanceof z.ZodError)return json({error:'Invalid request. Check the action, revision, and supplied fields.'},400);
  console.error('REDRAFT request failed',error instanceof Error?error.name:'UnknownError');
  return json({error:'The request could not be completed. Your last saved state is preserved.'},503);
}
async function limited(owner:string){
  const minute=Math.floor(Date.now()/60000),id=`${owner}:${minute}`;
  const row=await db().prepare('INSERT INTO rate_windows (id,count,expires_at) VALUES (?,1,?) ON CONFLICT(id) DO UPDATE SET count=count+1 RETURNING count').bind(id,(minute+2)*60000).first<{count:number}>();
  if((row?.count??0)>240)throw new HttpError(429,'Too many requests. Wait a minute and resume your saved draft.');
  if(row?.count===1)await db().prepare('DELETE FROM rate_windows WHERE expires_at < ?').bind(Date.now()).run();
}
async function readBody(request:Request){
  const origin=request.headers.get('origin');
  if(origin&&origin!==new URL(request.url).origin)throw new HttpError(403,'Cross-origin changes are not permitted.');
  if(request.headers.get('sec-fetch-site')==='cross-site')throw new HttpError(403,'Cross-site changes are not permitted.');
  if(!request.headers.get('content-type')?.toLowerCase().startsWith('application/json'))throw new HttpError(415,'Send application/json.');
  if(Number(request.headers.get('content-length'))>16000)throw new HttpError(413,'Request is too large.');
  const reader=request.body?.getReader();if(!reader)throw new HttpError(400,'Missing request body.');
  const chunks:Uint8Array[]=[];let length=0;
  while(true){const{value,done}=await reader.read();if(done)break;length+=value.length;if(length>16000){await reader.cancel();throw new HttpError(413,'Request is too large.');}chunks.push(value);}
  const bytes=new Uint8Array(length);let at=0;for(const chunk of chunks){bytes.set(chunk,at);at+=chunk.length;}
  try{return JSON.parse(new TextDecoder().decode(bytes));}catch{throw new HttpError(400,'Invalid JSON.');}
}
const base={id:z.string().uuid(),revision:z.number().int().nonnegative(),requestId:z.string().uuid()};
const pickId=z.string().regex(/^bp_[a-f0-9]{32}$/);
const schema=z.discriminatedUnion('action',[
  z.object({action:z.literal('new'),requestId:z.string().uuid(),mode:z.enum(['historical','daily']).default('historical'),team:z.string().max(4).optional(),year:z.number().int().refine(value=>years.includes(value)).optional(),seed:z.string().min(1).max(80).optional()}).strict(),
  z.object({action:z.literal('advance'),...base,pace:z.enum(['user','one']).default('user')}).strict(),
  z.object({action:z.literal('pick'),...base,prospectId:pickId}).strict(),
  z.object({action:z.literal('scout'),...base,prospectId:pickId}).strict(),
  z.object({action:z.literal('board'),...base,prospectIds:z.array(pickId).max(100)}).strict(),
  z.object({action:z.literal('trade'),...base,target:z.string().min(2).max(4),give:z.array(z.number().int().min(1).max(400)).min(1).max(20),receive:z.array(z.number().int().min(1).max(400)).min(1).max(20),accept:z.boolean()}).strict(),
  z.object({action:z.literal('simulate'),...base}).strict(),
  z.object({action:z.literal('save'),...base}).strict(),
]);
async function run(owner:string,id:string){const row=await db().prepare('SELECT id,owner,challenge_date,state,revision FROM game_runs WHERE id=? AND owner=?').bind(id,owner).first<RunRow>();if(!row)throw new HttpError(404,'Draft not found.');return row;}
const unpack=(row:RunRow)=>JSON.parse(row.state) as StoredGame;
function compatible(game:StoredGame,bundle=getScenario(game.year)){return game.modelVersion===bundle.models.version&&game.datasetVersion===bundle.dataset.metadata.version&&game.engineVersion===RULE_VERSION&&game.scoringVersion===SCORING_VERSION&&game.scoutingVersion===BLIND_POLICY_VERSION&&game.ensembleSize===ENSEMBLE_SIZE;}
function remap(value:unknown,aliases:AliasCatalog):unknown{
  if(typeof value==='string')return aliases.toPublic.get(value)??value;
  if(Array.isArray(value))return value.map(v=>remap(v,aliases));
  if(value&&typeof value==='object')return Object.fromEntries(Object.entries(value).filter(([key])=>key!=='blindSalt').map(([key,v])=>[key,remap(v,aliases)]));
  return value;
}
async function view(game:StoredGame){
  const {dataset,models,scoutingPolicy,teamContexts,teamContextMetadata,selectedTeamContext}=getScenario(game.year);
  const aliases=await aliasCatalog(game.blindSalt,dataset),revealed=identityRevealed(game);
  const publicGame=remap(game,aliases) as Record<string,unknown>;
  if(game.status==='drafting'||(game.mode==='daily'&&game.createdAt.slice(0,10)===utcDate()))publicGame.seed='Hidden until challenge closes or draft reveal';
  if(game.status==='simulating'&&game.results){publicGame.results={...game.results,replicates:game.results.replicates.map(r=>({index:r.index,baseline:{...r.baseline,seasons:[]},alternate:{...r.alternate,seasons:[]}}))};}
  // Actual draft allocation in baseline player rows is itself an identity clue.
  if(!revealed&&game.status==='complete'&&game.results){
    const masked={...game.results,replicates:game.results.replicates.map(r=>({...r,baseline:{...r.baseline,seasons:r.baseline.seasons.map(s=>({...s,players:[],starPicks:[],awards:[]}))}}))};
    publicGame.results=remap(masked,aliases);
  }
  let prospects=prospectViews(game,dataset,models,scoutingPolicy,aliases);
  const ok=compatible(game);
  if(!ok)prospects=prospects.map(p=>({...p,projection:{...p.projection,roleProbability:null,roleProbabilityLabel:'Model version unavailable',modelVersion:game.modelVersion,supported:false,fallback:true}}));
  return {game:{...publicGame,ensembleTarget:ENSEMBLE_SIZE,identityRevealed:revealed},prospects,teams:dataset.teams,teamContexts,teamContextMetadata,selectedTeamContext:selectedTeamContext(game.team),
    ...(revealed?{historicalSelections:remap(dataset.actualPicks,aliases)}:{}),
    ...(!ok?{compatibilityWarning:'This saved run uses a retired model or dataset. Review is available; further changes are disabled.'}:{})};
}
async function challenge():Promise<DailyConfig>{
  const date=utcDate();let row=await db().prepare('SELECT config FROM daily_challenges WHERE date=?').bind(date).first<{config:string}>();
  if(!row){const year=years[Math.floor(random('daily-year-v1',date)*years.length)],bundle=getScenario(year),config:DailyConfig={date,team:bundle.dataset.teams[Math.floor(random('daily-team-v1',date)*bundle.dataset.teams.length)].id,year,seed:token(),blindSalt:token(),modelVersion:String(bundle.models.version),datasetVersion:String(bundle.dataset.metadata.version),engineVersion:RULE_VERSION,scoringVersion:SCORING_VERSION,scoutingVersion:BLIND_POLICY_VERSION,ensembleSize:ENSEMBLE_SIZE};
    await db().prepare('INSERT INTO daily_challenges (date,config,created_at) VALUES (?,?,?) ON CONFLICT(date) DO NOTHING').bind(date,JSON.stringify(config),new Date().toISOString()).run();
    row=await db().prepare('SELECT config FROM daily_challenges WHERE date=?').bind(date).first<{config:string}>();
  }if(!row)throw new HttpError(503,'The daily challenge is unavailable.');return JSON.parse(row.config);
}
async function scoreIfNeeded(row:RunRow,game:StoredGame){
  if(game.mode!=='daily'||game.status!=='complete'||!game.results||!row.challenge_date)return;
  const score=game.results.decisionScore;if(!Number.isFinite(score)||score<0||score>100||game.results.replicates.length!==game.ensembleSize)throw new HttpError(503,'Result validation failed.');
  await db().prepare('INSERT INTO daily_leaderboard_entries (id,date,owner,game_id,alias,team,score,model_version,dataset_version,created_at) SELECT ?,?,?,?,?,?,?,?,?,? WHERE EXISTS (SELECT 1 FROM daily_attempts WHERE owner=? AND date=? AND game_id=?) ON CONFLICT(owner,date) DO NOTHING').bind(crypto.randomUUID(),row.challenge_date,row.owner,game.id,await alias(row.owner),game.team,score,game.modelVersion,game.datasetVersion,new Date().toISOString(),row.owner,row.challenge_date,game.id).run();
}
export async function GET(request:Request){try{
  const owner=await identity();await limited(owner);const url=new URL(request.url),action=url.searchParams.get('action')??'bootstrap';
  if(action==='load'){const row=await run(owner,url.searchParams.get('id')??'');const game=unpack(row);await scoreIfNeeded(row,game);return json(await view(game));}
  if(!['bootstrap','history','leaderboard'].includes(action))throw new HttpError(400,'Unknown action.');
  const daily=await challenge();
  const [history,leaders,attempt]=await Promise.all([
    db().prepare('SELECT id,team,year,mode,status,updated_at AS updatedAt,score FROM game_runs WHERE owner=? ORDER BY updated_at DESC LIMIT 30').bind(owner).all(),
    db().prepare('SELECT alias,score,team FROM daily_leaderboard_entries WHERE date=? ORDER BY score DESC,created_at ASC LIMIT 100').bind(daily.date).all(),
    db().prepare('SELECT a.game_id,g.status FROM daily_attempts a JOIN game_runs g ON g.id=a.game_id WHERE a.owner=? AND a.date=?').bind(owner,daily.date).first<{game_id:string;status:string}>(),
  ]);
  const leaderboard=rankLeaderboard(leaders.results as {alias:string;score:number;team:string}[]);
  if(action==='leaderboard')return json({leaderboard});if(action==='history')return json({history:history.results});
  const teamsByYear=Object.fromEntries(years.map(year=>[year,getScenario(year).dataset.teams]));
  const teamContextsByYear=Object.fromEntries(years.map(year=>[year,getScenario(year).teamContexts]));
  const teamContextMetadataByYear=Object.fromEntries(years.map(year=>[year,getScenario(year).teamContextMetadata]));
  const scenarioModelsByYear=Object.fromEntries(years.map(year=>{const bundle=getScenario(year);return [year,{modelVersion:bundle.models.version,datasetVersion:bundle.dataset.metadata.version,modelStatus:year===2018?'research-alpha':'pre-2018-logistic-extrapolation',teamContextAvailable:year===2018}]}));
  return json({teams:dataset.teams,teamsByYear,teamContextsByYear,teamContextMetadataByYear,teamContexts,teamContextMetadata,selectedTeamContext:null,years,coverage,scenarioModelsByYear,daily:{date:daily.date,team:daily.team,year:daily.year,endsAt:Date.parse(daily.date+'T00:00:00Z')+86400000,status:attempt?.status??'available',gameId:attempt?.game_id},history:history.results,leaderboard,user:{alias:await alias(owner)},methodology:{version:models.version,datasetVersion:dataset.metadata.version,ensembleSize:ENSEMBLE_SIZE,scoutingVersion:BLIND_POLICY_VERSION,status:'Research alpha',coverage:`Playable scenario years: ${years.join(', ')}. Other years are not enabled; check coverage for blockers.`,limitations:['All post-2018 classes use a frozen model trained through 2017, extrapolated without cohort-specific calibration; reference-only, unseen-position, and specialist rows use explicit fallbacks or remain unavailable.','No audited draft-day roster/position-use context is wired to post-2018 scenarios.','2026 season outcomes are incomplete; five-year labels for that draft class do not yet exist.','Shared profiles reduce identity clues; they do not guarantee anonymity.','The trained target is rookie participation, not five-year talent.','Five-year development, roster turnover, and CPU strategy remain explicit model assumptions.','Contracts, complete historical rosters, college production, and future-pick trades are not implemented.']}});
}catch(error){return failure(error);}}
export async function POST(request:Request){try{
  const owner=await identity();const payload=schema.parse(await readBody(request));await limited(owner);
  const requestHash=await hash(JSON.stringify(payload));
  const receipt=await db().prepare('SELECT owner,game_id,request_hash FROM request_receipts WHERE id=?').bind(payload.requestId).first<{owner:string;game_id:string;request_hash:string}>();
  if(receipt){if(receipt.owner!==owner||receipt.request_hash!==requestHash)throw new HttpError(409,'Request identifier was already used for another action.');const row=await run(owner,receipt.game_id);const game=unpack(row);await scoreIfNeeded(row,game);return json(await view(game));}
  if(payload.action==='new'){
    let config:DailyConfig|undefined;
    if(payload.mode==='daily'){
      if(payload.seed||payload.team||payload.year)throw new HttpError(400,'Daily conditions cannot be changed.');config=await challenge();
      const existing=await db().prepare('SELECT game_id FROM daily_attempts WHERE owner=? AND date=?').bind(owner,config.date).first<{game_id:string}>();
      if(existing)return json(await view(unpack(await run(owner,existing.game_id))));
      const pinned=getScenario(config.year);
      if(config.modelVersion!==pinned.models.version||config.datasetVersion!==pinned.dataset.metadata.version||config.engineVersion!==RULE_VERSION||config.scoutingVersion!==BLIND_POLICY_VERSION||config.scoringVersion!==SCORING_VERSION||config.ensembleSize!==ENSEMBLE_SIZE)throw new HttpError(409,'Today’s challenge is pinned to a different version. It remains frozen until the next UTC day.');
    }
    const year=config?.year??payload.year??2018,bundle=getScenario(year),{dataset,models}=bundle;
    if(payload.team&&!dataset.teams.some(t=>t.id===payload.team))throw new HttpError(400,'Unsupported historical franchise for this draft year.');
    const now=new Date().toISOString();const game:StoredGame={...createGame({id:crypto.randomUUID(),team:config?.team??payload.team,year,seed:config?.seed??payload.seed??token(),mode:payload.mode,now,modelVersion:String(models.version)},dataset),blindSalt:config?.blindSalt??token(),scoutingVersion:BLIND_POLICY_VERSION};
    const statements=[db().prepare('INSERT INTO game_runs (id,owner,mode,challenge_date,team,year,status,revision,state,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)').bind(game.id,owner,game.mode,config?.date??null,game.team,game.year,game.status,0,JSON.stringify(game),now,now),db().prepare('INSERT INTO request_receipts (id,owner,game_id,request_hash,created_at) VALUES (?,?,?,?,?)').bind(payload.requestId,owner,game.id,requestHash,now)];
    if(config)statements.push(db().prepare('INSERT INTO daily_attempts (id,owner,date,game_id,created_at) VALUES (?,?,?,?,?)').bind(crypto.randomUUID(),owner,config.date,game.id,now));
    try{await db().batch(statements);}catch{throw new HttpError(409,'Another request created this draft. Refresh your saved drafts.');}
    return json(await view(game),201);
  }
  const row=await run(owner,payload.id),game=unpack(row);
  const {dataset,models,scoutingPolicy}=getScenario(game.year);
  if(payload.revision!==row.revision)throw new HttpError(409,'Your saved draft changed. Reload it before continuing.');
  if(!compatible(game))throw new HttpError(409,'This saved draft uses a different version and is available for review only.');
  if(game.mode==='daily'&&row.challenge_date!==utcDate())throw new HttpError(409,'This daily challenge has closed. Your saved draft remains available for review.');
  validateGame(game,dataset);const aliases=await aliasCatalog(game.blindSalt,dataset);
  const canonical=(id:string)=>{const found=aliases.toCanonical.get(id);if(!found)throw new HttpError(400,'Unknown blind prospect identifier.');return found;};
  let next:GameState=game,tradeEvaluation;
  try{
    switch(payload.action){
      case 'advance':next=advance(game,dataset,models,payload.pace);break;
      case 'scout':{
        const id=canonical(payload.prospectId),profile=scoutingPolicy.profiles[id];
        if(!profile)throw new HttpError(400,'This prospect is outside the playable pool.');
        if(profile.memberIds.some(member=>game.scouted.includes(member)))throw new HttpError(400,'This shared report is already unlocked.');
        next=scout(game,id,dataset);break;
      }
      case 'pick':next=select(game,canonical(payload.prospectId),dataset);break;
      case 'board':next=setBoard(game,payload.prospectIds.map(canonical),dataset);break;
      case 'trade':tradeEvaluation=proposeTrade(game,payload,dataset);if(!payload.accept)return json({...await view(game),tradeEvaluation});if(!tradeEvaluation.accepted)throw new HttpError(400,tradeEvaluation.reason);next=applyTrade(game,payload,dataset);break;
      case 'simulate':{
        if(!['ready','simulating','complete'].includes(game.status))throw new HttpError(400,'Finish all seven rounds before simulating.');
        if(game.status==='complete'){await scoreIfNeeded(row,game);return json(await view(game));}
        const reps=[...game.results?.replicates??[]];
        const end=Math.min(ENSEMBLE_SIZE,reps.length+4);while(reps.length<end){const rep=simulateReplicate(game,reps.length,dataset,models);reps.push(rep.index===0?rep:compactReplicate(rep,game.team));}
        const studied=new Set(game.scouted.flatMap(id=>scoutingPolicy.profiles[id]?.memberIds??[id]));
        next={...game,status:reps.length===ENSEMBLE_SIZE?'complete':'simulating',results:summarizeResults({...game,scouted:[...studied]},reps,dataset,models)};break;
      }
      case 'save':break;
    }
  }catch(error){if(error instanceof HttpError)throw error;throw new HttpError(400,error instanceof Error?error.message:'Invalid draft action.');}
  const saved:StoredGame={...next,blindSalt:game.blindSalt,scoutingVersion:game.scoutingVersion,revision:row.revision+1,updatedAt:new Date().toISOString()};validateGame(saved,dataset);
  const state=JSON.stringify(saved);if(new TextEncoder().encode(state).length>1800000)throw new HttpError(503,'Simulation storage budget exceeded. The completed draft remains saved.');
  const results=await db().batch([
    db().prepare('UPDATE game_runs SET state=?,status=?,revision=?,score=?,updated_at=? WHERE id=? AND owner=? AND revision=?').bind(state,saved.status,saved.revision,saved.status==='complete'?saved.results?.decisionScore??null:null,saved.updatedAt,saved.id,owner,row.revision),
    db().prepare('INSERT INTO request_receipts (id,owner,game_id,request_hash,created_at) SELECT ?,?,?,?,? WHERE EXISTS (SELECT 1 FROM game_runs WHERE id=? AND owner=? AND revision=? AND state=?)').bind(payload.requestId,owner,saved.id,requestHash,saved.updatedAt,saved.id,owner,saved.revision,state),
  ]);
  if(!results[0].meta.changes)throw new HttpError(409,'Another request updated this draft. Reload your saved state.');
  await scoreIfNeeded(row,saved);return json({...await view(saved),...(tradeEvaluation?{tradeEvaluation}:{})});
}catch(error){return failure(error);}}
