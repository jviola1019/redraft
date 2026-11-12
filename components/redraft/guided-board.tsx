'use client';
import {useEffect,useMemo,useState} from 'react';
import {ArrowRight,Bookmark,Check,Eye,Shuffle} from 'lucide-react';
import {measurement,positionHelp,roleLabel,type ProspectView} from './types';
export const positionNames:Record<string,string>={QB:'Quarterback',RB:'Running back',WR:'Wide receiver',TE:'Tight end',OL:'Offensive line',DL:'Defensive line',LB:'Linebacker',DB:'Defensive back',ST:'Special teams'};
type Props={prospects:ProspectView[];board:string[];compareIds:string[];busy:boolean;scoutingPoints:number;myTurn:boolean;onDetail:(id:string)=>void;onScout:(id:string)=>void;onCompare:(id:string)=>void;draftCounts:{position:string;count:number}[]};
export default function GuidedBoard(p:Props){
  const [offset,setOffset]=useState(0),[count,setCount]=useState(3);
  useEffect(()=>setOffset(0),[p.prospects.length]);
  const cards=useMemo(()=>{const ordered=[...p.prospects.slice(offset),...p.prospects.slice(0,offset)];const chosen:ProspectView[]=[];const seen=new Set<string>();for(const prospect of ordered){if(chosen.length>=count)break;if(!seen.has(prospect.position)){chosen.push(prospect);seen.add(prospect.position)}}for(const prospect of ordered){if(chosen.length>=count)break;if(!chosen.some(c=>c.id===prospect.id))chosen.push(prospect)}return chosen},[p.prospects,offset,count]);
  const draftedRoles = new Set(p.draftCounts.map(pick => pick.position));
  const scoutCandidates = cards.filter(prospect => !prospect.scouted);
  const suggested = p.scoutingPoints > 0
    ? scoutCandidates.find(prospect => !draftedRoles.has(prospect.position)) ?? scoutCandidates[0]
    : undefined;
  return <div className="guided-board" id="prospect-choices">
    <div className="guided-heading"><div><h2>{count===3?'Explore a few players':'A few more options'}</h2><p>Start with an unopened report. Compare its playing-time outlook with another role before choosing.</p></div><button className="btn small" disabled={p.prospects.length<2} onClick={()=>setOffset(o=>(o+1+Math.floor(Math.random()*(p.prospects.length-1)))%p.prospects.length)}><Shuffle size={15}/>Different profiles</button></div>
    <details className="blind-disclosure"><summary>How do I read these stats?</summary><p>A lower 40-yard time means a faster sprint. Height and weight describe size, not overall ability. These ranges describe a group of players. Scouting unlocks that group’s estimated chance of getting meaningful rookie playing time; it is not a career guarantee. The suggestion helps you explore a role you have not drafted—it is not a verified team need.</p></details>
    <div className="guided-cards">{cards.map(prospect=>{const studied=!!prospect.scouted;const newRole=!p.draftCounts.some(pick=>pick.position===prospect.position);return <article className={`guide-card ${studied?'studied':''}`} key={prospect.id}>
      <div className="guide-card-top"><span className="pixel-position">{prospect.position}</span><span className="mono">{prospect.blindName||'Blind prospect'}</span>{p.board.includes(prospect.id)&&<Bookmark size={16} fill="currentColor" aria-label="On your shortlist"/>}</div>
      {prospect.id===suggested?.id&&<span className="guide-new-role">Scout first · {newRole?'fills an undrafted role':'unopened report'}</span>}{newRole&&prospect.id!==suggested?.id&&<span className="guide-new-role">New role for your class</span>}<h3>{positionNames[prospect.position]||prospect.position}</h3><p className="guide-role">{positionHelp[prospect.position]?.replace(/^.*? — /,'')||'This role follows the shared scouting group.'}</p>
      <div className="guide-range-label">Shared group ranges</div><div className="guide-measurements"><div><span>Height · in</span><strong>{measurement(prospect,'height',false)}</strong></div><div><span>Weight · lb</span><strong>{measurement(prospect,'weight',false)}</strong></div><div><span>40 yards · sec</span><strong>{measurement(prospect,'forty',false)}</strong></div></div>
      <div className="guide-projection"><span>Rookie playing-time outlook</span><strong>{studied&&prospect.projection?roleLabel(prospect):studied?'Unavailable':'Not scouted yet'}</strong><p>{studied?'Group chance of 200+ rookie snaps (plays).':'1 point unlocks the outlook for all matching profiles.'}{studied&&(prospect.projection?.fallback||prospect.projection?.supported===false)&&<span className="guide-fallback">Limited evidence · fallback prior</span>}</p></div>
      <div className="guide-card-actions"><button className="btn" disabled={p.busy||studied||p.scoutingPoints<1} onClick={()=>p.onScout(prospect.id)}>{studied?<Check size={15}/>:<Eye size={15}/>} {studied?'Scouted':p.scoutingPoints<1?'No points left':'Scout · 1 point'}</button><button className="btn primary" disabled={p.busy} onClick={()=>p.onDetail(prospect.id)}>{p.myTurn?'Review & pick':'View profile'}<ArrowRight size={15}/></button></div>
      <label className="guide-compare"><input type="checkbox" checked={p.compareIds.includes(prospect.id)} disabled={p.compareIds.length>=3&&!p.compareIds.includes(prospect.id)} onChange={()=>p.onCompare(prospect.id)}/>Compare this profile</label>
    </article>})}</div>
    {!cards.length&&<p className="draft-empty">No available profiles match. Clear your search or choose another role.</p>}
    <div className="guided-footer"><p>{p.draftCounts.length?<>Your class:{' '}{p.draftCounts.map(x=>`${x.count} ${positionNames[x.position]||x.position}`).join(' · ')}</>:'Your first selection starts your new draft class.'}</p>{p.prospects.length>3&&<button className="text-button" onClick={()=>setCount(c=>c===3?6:3)}>{count===3?'Show six profiles':'Back to three'}<ArrowRight size={14}/></button>}</div>
  </div>;
}
