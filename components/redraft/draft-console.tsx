'use client';
import {useEffect,useRef,useState} from 'react';
import {ChevronRight,Loader2,Play} from 'lucide-react';

type Props={team:string;round:number;pick:number;completed:number;total:number;tradeCount:number;scoutingPoints:number;remainingPicks:number;lastSelection?:string;lastTrade?:string;myTurn:boolean;busy:boolean;onAdvance:(pace:'user'|'one')=>void};
export default function DraftConsole(p:Props){
  const prior=useRef({picks:p.completed,trades:p.tradeCount});
  const [event,setEvent]=useState<'idle'|'pick'|'trade'>('idle');
  const [eventKey,setEventKey]=useState(0);
  useEffect(()=>{const next=p.tradeCount>prior.current.trades?'trade':p.completed>prior.current.picks?'pick':'idle';prior.current={picks:p.completed,trades:p.tradeCount};if(next==='idle')return;setEvent(next);setEventKey(k=>k+1);const timer=setTimeout(()=>setEvent('idle'),1800);return()=>clearTimeout(timer)},[p.completed,p.tradeCount]);
  const update=event==='trade'?`Trade completed: ${p.lastTrade||'pick ownership updated'}.`:p.lastSelection?`Latest selection: ${p.lastSelection}.`:'The first selection is still open.';
  return <section className={`draft-console ${p.myTurn?'your-turn':''}`} aria-label="Current draft status">
    <div className="console-main"><div className="console-overline"><span>ROUND {p.round} OF 7</span><span>PICK {p.pick}</span><span className="console-turn">{p.myTurn?'YOUR TURN':'LEAGUE PICK'}</span></div><h2>{p.myTurn?'You’re up. Make your pick.':p.team}</h2><p>{p.myTurn?'Open a profile to review and select your player.':'Scout or trade now, or advance to your next selection.'}</p></div>
    <div className={`console-scene event-${event}`}><svg viewBox="0 0 240 76" aria-hidden="true" shapeRendering="crispEdges"><rect width="240" height="76" fill="#bcd2ac"/><path d="M0 5H240M0 18H240" stroke="#7da383" strokeWidth="5"/>{Array.from({length:16},(_,i)=><g key={i}><rect x={i*16+4} y="2" width="5" height="5" fill={i%2?'#c96a44':'#355e57'}/><rect x={i*16+1} y="7" width="11" height="7" fill={i%2?'#e2c483':'#6b9176'}/></g>)}<rect y="24" width="240" height="52" fill="#4b8559"/>{[20,60,100,140,180,220].map(x=><path key={x} d={`M${x} 32V70`} stroke="#bed6a0" strokeWidth="2"/>)}<path d="M0 28H240M0 72H240" stroke="#e6ebbc" strokeWidth="2"/><path d="M2 29H19V71H2ZM221 29H238V71H221Z" fill="#233d4b"/>
    <path d="M5 33H16M5 39H16M5 45H16M5 51H16M5 57H16M5 63H16M224 33H235M224 39H235M224 45H235M224 51H235M224 57H235M224 63H235" stroke="#56737a"/>
    <path d="M70 45h4m16 0h4m16 0h4m16 0h4m16 0h4m16 0h4M70 55h4m16 0h4m16 0h4m16 0h4m16 0h4m16 0h4" stroke="#e6ebbc"/>
    <path d="M120 38h5v2h3v5h-2v3h-4v3h-5v-2h-3v-5h2v-3h4z" fill="#783e2e"/>
    <path d="m118 46 6-5m-4 2 2 2" stroke="#fff0c4"/>
    <path d="M225 12v10h10V12m-5 10v9" fill="none" stroke="#efd27b" strokeWidth="2"/><g className={event==='pick'?'console-pick-walk':''} key={`pick-${eventKey}`}><rect x="24" y="27" width="15" height="10" fill="#fff0c4"/><rect x="24" y="25" width="16" height="4" fill="#193f4a"/><rect x="21" y="38" width="20" height="18" fill="#c94c36"/><rect x="26" y="42" width="9" height="3" fill="#fff0c4"/><path d="M26 56V67H22M36 56V67H40" fill="none" stroke="#193f4a" strokeWidth="5"/></g><rect x="199" y="47" width="27" height="20" fill="#193f4a"/><rect x="195" y="43" width="35" height="6" fill="#e9c56b"/>{event==='trade'&&<g className="console-trade" key={`trade-${eventKey}`}><rect x="43" y="35" width="19" height="13" fill="#fff0c4"/><path d="M43 35L52 43L62 35" fill="none" stroke="#b6422d" strokeWidth="2"/></g>}</svg><span className="sr-only" aria-live="polite">{update}</span></div>
    <div className="console-actions">{p.myTurn?<span className="console-ready"><span aria-hidden="true">↓</span> Choose below</span>:<><button className="btn primary" disabled={p.busy} onClick={()=>p.onAdvance('user')}>{p.busy?<Loader2 size={15} className="spinner"/>:<Play size={15}/>}Jump to my pick</button><button className="text-button" disabled={p.busy} onClick={()=>p.onAdvance('one')}>One pick at a time<ChevronRight size={15}/></button></>}</div>
    <div className="console-resources"><span><b>{p.scoutingPoints}</b> scouting points</span><span><b>{p.remainingPicks}</b> picks left</span><span>{p.completed} / {p.total} league picks made</span></div>
    <div className="console-progress" role="progressbar" aria-label="Draft selections completed" aria-valuemin={0} aria-valuemax={p.total} aria-valuenow={p.completed}><span style={{width:`${p.total?p.completed/p.total*100:0}%`}}/></div>
  </section>;
}
