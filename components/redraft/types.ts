import type { GameState, Team, Prospect, TradeEvaluation, Selection, PriorSeasonTeamContext } from '@/lib/types';
export type MeasurementKey = 'height'|'weight'|'forty'|'vertical'|'broad'|'bench'|'cone'|'shuttle';
export type ProspectView = Prospect & {
  blindName?: string;
  displayMeasurements?: Partial<Record<MeasurementKey,string>>;
  profileNotes?: string | string[];
  scouted?: boolean;
  projection?: { roleProbability: number | null; roleProbabilityLabel?: string; target: string; modelVersion: string; uncertainty: string; supported?: boolean; fallback?: boolean; projectionSource?: string } | null;
};
export type HistoryRow = {id:string;team:string;year:number;mode:string;status:string;updatedAt:string;score?:number};
export type PriorTeamContext = PriorSeasonTeamContext & {
  usagePolicy?:{label:string;coefficientCap:number;positionAdjustments:Record<string,number>;interpretation:string};
};
export type Bootstrap = {teamsByYear?:Record<string,Team[]>;teamContextsByYear?:Record<string,PriorTeamContext[]>;coverage?:{year:number;status:string;blockers?:string[]}[];teamContexts?:PriorTeamContext[];teams:Team[];years:number[];daily:{date:string;team:string;year:number;endsAt:string|number;status:string;gameId?:string};history:HistoryRow[];leaderboard:{rank:number;alias:string;score:number;team:string}[];methodology?:Record<string,unknown>;user?:{alias:string}};
export type Payload = {teamContexts?:PriorTeamContext[];selectedTeamContext?:PriorTeamContext|null;teamContextMetadata?:Record<string,unknown>;game:GameState & {ensembleTarget?:number;identityRevealed?:boolean;identityRevealAt?:string|number};prospects:ProspectView[];teams:Team[];tradeEvaluation?:TradeEvaluation;historicalSelections?:Selection[];compatibilityWarning?:string};
export const fmt=(n:number|null|undefined,d=0)=>n==null||!Number.isFinite(n)?'—':n.toFixed(d);
export const percent=(n:number|null|undefined)=>n==null?'Withheld':`${Math.round(n*100)}%`;
export const roleLabel=(p:ProspectView,revealed=false)=>p.projection?.roleProbabilityLabel||(revealed?percent(p.projection?.roleProbability):'Range withheld');
export const signed=(n:number|null|undefined,d=1)=>n==null?'—':`${n>0?'+':''}${n.toFixed(d)}`;
export const positionHelp:Record<string,string>={QB:'Quarterback — directs the passing offense and distributes the ball.',RB:'Running back — carries the ball, receives passes, and helps protect the quarterback.',WR:'Wide receiver — creates separation and catches passes.',TE:'Tight end — combines receiving and blocking responsibilities.',OT:'Offensive tackle — protects the edge of the offensive line.',OG:'Offensive guard — blocks in the interior offensive line.',G:'Guard — blocks in the interior offensive line.',C:'Center — snaps the ball and organizes interior protection.',OL:'Offensive line — protects the quarterback and opens running lanes.',DE:'Defensive end — defends the edge and pressures the passer.',DT:'Defensive tackle — defends the interior and disrupts the pocket.',DL:'Defensive line — contests the line of scrimmage and pressures the offense.',LB:'Linebacker — fits the run, covers receivers, and may rush the passer.',ILB:'Inside linebacker — defends the interior and covers underneath routes.',OLB:'Outside linebacker — defends the edge, rushes, or covers depending on role.',CB:'Cornerback — covers wide receivers and supports the run defense.',S:'Safety — protects deep space and supports coverage and run defense.',FS:'Free safety — usually protects deeper areas of the field.',SS:'Strong safety — combines coverage and run support.',DB:'Defensive back — covers receivers and protects space behind the defense.',K:'Kicker — handles field goals and extra points.',P:'Punter — kicks to change field position.',LS:'Long snapper — delivers the snap on punts and placekicks.',ST:'Special teams — kicker, punter, or long snapper. The specific role is withheld because it would narrow identity too sharply.',EDGE:'Edge defender — pressures the quarterback and defends outside runs.'};
export function measurement(p:ProspectView,key:MeasurementKey,revealed:boolean){
  if(!revealed) return p.displayMeasurements?.[key] || 'Withheld';
  const map:Record<MeasurementKey,number|null|undefined>={height:p.heightIn,weight:p.weightLb,forty:p.forty,vertical:p.verticalIn,broad:p.broadJumpIn,bench:p.bench,cone:p.cone,shuttle:p.shuttle};
  return fmt(map[key],['forty','cone','shuttle'].includes(key)?2:key==='vertical'?1:0);
}
export function requestUuid(){
  if(typeof globalThis.crypto?.randomUUID==='function')return globalThis.crypto.randomUUID();
  const b=new Uint8Array(16);globalThis.crypto.getRandomValues(b);b[6]=(b[6]&15)|64;b[8]=(b[8]&63)|128;
  const h=Array.from(b,x=>x.toString(16).padStart(2,'0'));return `${h.slice(0,4).join('')}-${h.slice(4,6).join('')}-${h.slice(6,8).join('')}-${h.slice(8,10).join('')}-${h.slice(10).join('')}`;
}
