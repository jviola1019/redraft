'use client';
import {useEffect,useRef,useState} from 'react';

type Props={scene:'welcome'|'setup'|'simulation'|'season';teamLabel?:string;progress?:number;total?:number;year?:number;record?:string;champion?:boolean};
const glyphs:Record<string,string[]>={R:['11110','10001','10001','11110','10100','10010','10001'],E:['11111','10000','10000','11110','10000','10000','11111'],D:['11110','10001','10001','10001','10001','10001','11110'],A:['01110','10001','10001','11111','10001','10001','10001'],F:['11111','10000','10000','11110','10000','10000','10000'],T:['11111','00100','00100','00100','00100','00100','00100']};
export function PixelLogo(){return <svg viewBox="0 0 41 7" width="164" height="28" fill="currentColor" aria-hidden="true" shapeRendering="crispEdges">{'REDRAFT'.split('').flatMap((c,i)=>glyphs[c].flatMap((row,y)=>row.split('').map((v,x)=>v==='1'?<rect key={`${i}-${x}-${y}`} x={i*6+x} y={y} width="1" height="1"/>:null)))}</svg>}
function Player({x=0,y=0,shirt='#d65236',mirror=false}:{x?:number;y?:number;shirt?:string;mirror?:boolean}){return <g transform={`translate(${x} ${y}) ${mirror?'scale(-1 1)':''}`} shapeRendering="crispEdges"><rect x="8" y="0" width="24" height="8" fill="#173b48"/><rect x="4" y="8" width="32" height="16" fill="#fff0c4"/><rect x="4" y="8" width="8" height="12" fill="#173b48"/><rect x="28" y="12" width="8" height="4" fill="#173b48"/><rect x="12" y="24" width="16" height="4" fill="#edb77f"/><rect x="8" y="28" width="24" height="28" fill={shirt}/><rect x="0" y="32" width="8" height="20" fill={shirt}/><rect x="32" y="32" width="8" height="20" fill={shirt}/><rect x="0" y="52" width="8" height="8" fill="#edb77f"/><rect x="32" y="52" width="8" height="8" fill="#edb77f"/><rect x="12" y="32" width="12" height="4" fill="#fff0c4"/><rect x="8" y="56" width="24" height="8" fill="#fff0c4"/><g className="pixel-legs"><rect x="8" y="64" width="8" height="16" fill="#173b48"/><rect x="24" y="64" width="8" height="16" fill="#173b48"/><rect x="4" y="80" width="12" height="4" fill="#173b48"/><rect x="24" y="80" width="12" height="4" fill="#173b48"/></g></g>}
export const stadiumColors = {
  sky: '#183742', horizon: '#284a50', stands: '#335a58', rail: '#a4bd9b',
  turf: '#39734e', stripe: '#316646', chalk: '#d8e8ba', gold: '#efc875',
  crowd: ['#a5bc98', '#dda76e', '#759f89', '#c9745c'],
};

export default function PixelStadium({ scene, teamLabel, progress = 0, total = 256, year, record, champion }: Props) {
  const previous = useRef({ progress, year });
  const [motion, setMotion] = useState(0);
  useEffect(() => {
    if (progress > previous.current.progress || (scene === 'season' && year !== previous.current.year)) {
      setMotion(value => value + 1);
    }
    previous.current = { progress, year };
  }, [progress, scene, year]);

  const title = scene === 'welcome' ? 'THE PICK IS YOURS'
    : scene === 'setup' ? year ? `${year} NFL DRAFT` : 'HISTORICAL DRAFT'
    : scene === 'season' ? `${year} SEASON` : 'SIMULATING SEASONS';
  const sub = scene === 'season' ? `${teamLabel || 'YOUR TEAM'} / ${record || ''}`
    : scene === 'simulation' ? `${progress} OF ${total} PAIRED RUNS` : '';
  const caption = scene === 'simulation' ? `${progress} of ${total} paired simulations saved.`
    : scene === 'season' ? `${year}: ${record}. ${champion ? 'Simulated champion.' : 'One simulated season.'}` : '';
  const fraction = total > 0 ? Math.max(0, Math.min(1, progress / total)) : 0;
  const c = stadiumColors;

  return <figure className={`pixel-stadium scene-${scene}`}>
    <svg viewBox="0 0 720 376" role={caption ? 'img' : undefined} aria-label={caption || undefined} aria-hidden={!caption} shapeRendering="crispEdges">
      <rect width="720" height="376" fill={c.sky}/>
      <path d="M0 89H40V66H64V44H108V56H126V88H168V72H211V101H512V75H553V57H602V38H643V64H683V54H709V83H720V182H0Z" fill={c.horizon}/>
      <path d="M0 122H720V251H0Z" fill={c.stands}/>
      {[0, 1, 2, 3].map(row => <g key={row}>
        <rect y={150 + row * 23} width="720" height="3" fill={c.rail} opacity=".45"/>
        {Array.from({length: 38}, (_, i) => <path key={i} d={`M${i * 19 + row % 2 * 5} ${137 + row * 23}h5v5h3v6h-11v-6h3z`} fill={c.crowd[(i * (row + 1) + i % 5 + row) % c.crowd.length]}/>)}
      </g>)}
      {[56, 664].map(x => <g key={x} transform={`translate(${x} 0)`}>
        <path d="M-3 59H3V224H-3ZM-34 43H34V63H-34Z" fill="#101f29"/>
        <path d="M-30 47H30V59H-30Z" fill={c.gold}/>
        <path d="M-19 47V59M-7 47V59M7 47V59M19 47V59" stroke="#586964" strokeWidth="3"/>
      </g>)}
      <path d="M159 17H561V120H159Z" fill="#111f28"/>
      <path d="M166 23H554V113H166Z" fill="#557368"/>
      <path d="M172 30H548V106H172Z" fill="#142d36"/>
      <path d="M180 37H540V40H180ZM180 97H540V100H180Z" fill="#426459"/>
      <path d="M182 50h8v8h-8zM530 50h8v8h-8z" fill={c.gold}/>
      <text x="360" y={sub ? 66 : 79} textAnchor="middle" fill="#fff1c8" fontFamily="monospace" fontWeight="bold" fontSize="25">{title}</text>
      {sub && <text x="360" y="89" textAnchor="middle" fill="#c5dcad" fontFamily="monospace" fontSize="15">{sub.slice(0, 39)}</text>}
      <rect y="224" width="720" height="12" fill="#172e34"/>
      <path d="M0 228H720" stroke={c.gold} strokeWidth="3" strokeDasharray="11 4"/>
      <rect y="236" width="720" height="140" fill={c.turf}/>
      {[0, 160, 320, 480, 640].map(x => <rect key={x} x={x} y="242" width="80" height="124" fill={c.stripe}/>)}
      <path d="M0 244H720M0 365H720" stroke={c.chalk} strokeWidth="3"/>
      {[0, 80, 160, 240, 320, 400, 480, 560, 640, 720].map(x => <g key={x}>
        <path d={`M${x} 245V365`} stroke={c.chalk} strokeWidth="2" opacity=".62"/>
        <path d={`M${x - 4} 281h9m-9 47h9`} stroke={c.chalk} strokeWidth="2"/>
      </g>)}
      <path d="M307 283H413V338H307Z" fill="#244c3a"/>
      <path d="M309 281H411V335H309Z" fill="#38624a" stroke={c.chalk} strokeWidth="2"/>
      <path d="M339 309H346V302H353V295H370V302H377V309H370V316H363V323H346V316H339Z" fill="#96664e"/>
      <path d="M351 315l13-13m-12 5l5 5m0-9l5 5" stroke="#fff1c8" strokeWidth="2"/>
      <path d="M42 212V242h31v-30m-15 30v43h-12" fill="none" stroke={c.gold} strokeWidth="5"/>
      <path d="M647 212V242h31v-30m-15 30v43h12" fill="none" stroke={c.gold} strokeWidth="5"/>
      <g className={motion ? 'season-run' : undefined} key={motion}><Player x={133} y={242} shirt="#c94c36"/></g>
      <Player x={601} y={240} shirt="#bf9951" mirror/>
      <path d="M568 305H625V330H568ZM562 299H631V306H562Z" fill="#172e34"/>
      <path d="M562 298H631V304H562Z" fill={c.gold}/>
      {scene === 'simulation' && <><rect x="214" y="131" width="292" height="14" fill="#132b32"/><rect className="stadium-progress" x="218" y="135" width={284 * fraction} height="6" fill={c.gold}/></>}
    {champion&&<g transform="translate(324 165)"><rect x="12" width="48" height="8" fill="#f5cc63"/><rect x="16" y="8" width="40" height="20" fill="#f5cc63"/><rect x="24" y="28" width="24" height="8" fill="#e3a43d"/><rect x="32" y="36" width="8" height="16" fill="#f5cc63"/><rect x="20" y="52" width="32" height="8" fill="#e3a43d"/><rect x="4" y="8" width="8" height="20" fill="#f5cc63"/><rect x="60" y="8" width="8" height="20" fill="#f5cc63"/></g>}
    </svg>
    {caption && <figcaption aria-live="polite">{caption}</figcaption>}
  </figure>;
}
