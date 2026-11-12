'use client';
/** Original geometric sprites; no third-party game or team artwork. */
export function PixelField({progress=0,label='THE NEXT CHAPTER IS YOURS'}:{progress?:number;label?:string}) {
 const x=24+Math.max(0,Math.min(1,progress))*240;
 return <div className="pixel-stadium legacy-pitch"><div className="pixel-caption">{label}</div><svg viewBox="0 0 320 144" role="img" aria-label="Pixel football field showing draft progress" shapeRendering="crispEdges">
 <rect width="320" height="144" fill="#132f39"/>
 {Array.from({length:32},(_,i)=><rect key={i} x={i*10} y={8+(i%3)*4} width="6" height="4" fill={i%2?'#f0c76b':'#6a9a8b'}/>)}
 <rect x="8" y="32" width="304" height="104" fill="#27594d"/>
 {Array.from({length:10},(_,i)=><rect key={i} x={24+i*28} y="36" width="1" height="96" fill="#73a288"/>)}
 <path d="M8 36H312M8 132H312M160 36V132" stroke="#d9dfae" strokeWidth="2"/>
 <g className="pixel-runner" style={{transform:`translate(${x}px,70px)`}}>
 <path d="M4 0H16V4H20V12H16V16H4V12H0V4H4Z" fill="#f0c76b"/><path d="M12 6H24V10H12Z" fill="#162d35"/>
 <path d="M4 16H16V20H20V32H0V20H4Z" fill="#ed7052"/><rect x="7" y="20" width="5" height="8" fill="#fff0ca"/>
 <path d="M2 32H8V42H0V38H2M12 32H18V38H22V42H12Z" fill="#e9dfbd"/>
 <rect x="22" y="20" width="10" height="6" fill="#be774b"/>
 </g></svg><div className="pixel-caption pixel-caption-bottom">SCOUT → DRAFT → REWRITE</div></div>
}
