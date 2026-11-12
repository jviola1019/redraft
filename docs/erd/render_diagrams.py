"""Exact vector documentation, generated deterministically from declared relationships."""
from pathlib import Path
from html import escape
import sqlite3
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/erd';OUT.mkdir(exist_ok=True)
c=sqlite3.connect(':memory:');c.executescript((ROOT/'docs/warehouse/001_analytical_schema.sql').read_text())
def render(name,title,subtitle,nodes,edges):
 width=1240;height=155+(max(n[3] for n in nodes)+1)*175
 loc={n[0]:(35+n[2]*305,145+n[3]*175) for n in nodes}
 m=['erDiagram'];s=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',f'<title id="title">{escape(title)}</title><desc id="desc">{escape(subtitle)}</desc>',f'<rect width="{width}" height="{height}" fill="#f5f2e9"/>','<style>text{font-family:Arial,sans-serif}.name{font-size:14px;font-weight:700;fill:#1c2927}.field{font-family:monospace;font-size:11px;fill:#526052}.edge{fill:none;stroke:#a4aaa0;stroke-width:1.5}</style>',f'<text x="35" y="35" font-size="12" letter-spacing="3" fill="#b53429">REDRAFT / DATA ARCHITECTURE</text><text x="35" y="75" font-size="29" font-weight="700" fill="#1c2927">{escape(title)}</text><text x="35" y="108" font-size="13" fill="#526052">{escape(subtitle)}</text>']
 for a,b,label in edges:
  x,y=loc[a];xx,yy=loc[b];start=(x+135,y+125);end=(xx+135,yy)
  s.append(f'<path class="edge" d="M {start[0]} {start[1]} C {start[0]} {start[1]+25}, {end[0]} {end[1]-25}, {end[0]} {end[1]}"/><circle cx="{end[0]}" cy="{end[1]}" r="3" fill="#b53429"/>')
  m.append(f'  {a} ||--o{{ {b} : "{label}"')
 for node,fields,col,row in nodes:
  x,y=loc[node];m.append(f'  {node} {{');m.extend('    '+f for f in fields);m.append('  }')
  s.append(f'<rect x="{x}" y="{y}" width="270" height="125" rx="6" fill="#fffdf8" stroke="#d6d8cc"/><rect x="{x}" y="{y}" width="4" height="125" fill="#b53429"/><text class="name" x="{x+15}" y="{y+26}">{escape(node)}</text><path d="M {x+15} {y+39} H {x+255}" stroke="#deded3"/>')
  for i,f in enumerate(fields[:4]):s.append(f'<text class="field" x="{x+15}" y="{y+59+i*16}">{escape(f)}</text>')
 s.append('</svg>');(OUT/f'{name}.svg').write_text('\n'.join(s));(OUT/f'{name}.mmd').write_text('\n'.join(m)+'\n')
render('conceptual','Evidence, disclosure and alternate history','Facts and estimates are separate; identity suppression is a server response boundary.',[
 ('Sources',['text source_id PK','text rights','timestamp available_at'],0,0),('HistoricalFacts',['text dataset_version PK','text canonical_entity','text provenance'],1,0),
 ('Features',['text feature_version PK','timestamp cutoff','text units'],0,1),('ObservedOutcomes',['text player_season PK','timestamp label_available_at'],1,1),('DisclosurePolicy',['text version PK','text permitted_fields','text true_bands'],2,1),
 ('Models',['text model_version PK','timestamp training_cutoff'],0,2),('PrivateGame',['text game_id PK','text canonical_ids','text public_id_map'],1,2),('PublicDTO',['text per_run_id PK','text permitted_evidence'],2,2),
 ('Baseline',['text replicate_id PK','text actual_selections','text paired_seed'],0,3),('Alternate',['text replicate_id PK','text user_selections','text paired_seed'],1,3),
 ('Comparison',['text run_id PK','text historical_actuals','text paired_distribution'],1,4)],
 [('Sources','HistoricalFacts','documents'),('HistoricalFacts','Features','derives'),('HistoricalFacts','ObservedOutcomes','observes'),('Features','Models','fits'),('ObservedOutcomes','Models','evaluates'),('DisclosurePolicy','PublicDTO','constrains'),('PrivateGame','PublicDTO','sanitizes'),('Models','Baseline','generates'),('Models','Alternate','generates'),('PrivateGame','Alternate','changes'),('Baseline','Comparison','compares'),('Alternate','Comparison','compares')])
logical=[('data_sources',0,0),('players',1,0),('teams',2,0),('dataset_versions',3,0),('source_documents',0,1),('prospects',1,1),('team_identities',2,1),('model_versions',3,1),('feature_values',0,2),('historical_draft_picks',1,2),('game_runs',2,2),('disclosure_policies',3,2),('game_draft_picks',0,3),('simulation_runs',1,3),('game_public_prospect_ids',2,3),('daily_challenges',3,3)]
def attrs(table):
 fks={r[3] for r in c.execute(f'pragma foreign_key_list({table})')};cols=list(c.execute(f'pragma table_info({table})'));selected=sorted(cols,key=lambda r:(not bool(r[5]),not(r[1] in fks),r[0]))[:4]
 return [f'{r[2].lower()} {r[1]}'+(' PK' if r[5] else ' FK' if r[1] in fks else '') for r in selected]
render('logical','Logical ERD — principal families','Core relationships only; physical-full.mmd contains every analytical table and foreign key.',[(t,attrs(t),x,y) for t,x,y in logical],[('data_sources','source_documents','publishes'),('players','prospects','eligible'),('teams','team_identities','dated names'),('dataset_versions','model_versions','fits'),('source_documents','feature_values','evidence'),('prospects','historical_draft_picks','actual selections'),('model_versions','game_runs','pins'),('game_runs','game_draft_picks','contains'),('game_runs','simulation_runs','generates'),('game_runs','game_public_prospect_ids','private map'),('disclosure_policies','daily_challenges','pins')])
physical=[('dataset_versions',0,0),('model_versions',1,0),('disclosure_policies',2,0),('game_runs',0,1),('daily_challenges',1,1),('prospects',2,1),('game_pick_assets',0,2),('daily_attempts',1,2),('game_public_prospect_ids',2,2),('game_draft_picks',0,3),('daily_leaderboard_entries',1,3),('simulation_runs',2,3)]
render('physical','Physical core — keys and isolation','52-table analytical target; runtime D1 aggregates are a separate schema with separate tests.',[(t,attrs(t),x,y) for t,x,y in physical],[('dataset_versions','game_runs','version'),('model_versions','game_runs','version'),('disclosure_policies','daily_challenges','immutable'),('game_runs','game_pick_assets','owns'),('daily_challenges','daily_attempts','one per user'),('prospects','game_public_prospect_ids','private canonical key'),('game_pick_assets','game_draft_picks','owner validated'),('daily_attempts','daily_leaderboard_entries','immutable score'),('game_runs','simulation_runs','version match')])
full=['erDiagram'];tables=[r[0] for r in c.execute("select name from sqlite_master where type='table' order by name")]
for t in tables:
 fks={r[3] for r in c.execute(f'pragma foreign_key_list({t})')};full.append(f'  {t} {{')
 for r in c.execute(f'pragma table_info({t})'):full.append(f'    {r[2].lower()} {r[1]}'+(' PK' if r[5] else ' FK' if r[1] in fks else ''))
 full.append('  }')
for t in tables:
 for r in c.execute(f'pragma foreign_key_list({t})'):full.append(f'  {r[2]} ||--o{{ {t} : "{r[3]}"')
(OUT/'physical-full.mmd').write_text('\n'.join(full)+'\n');print(f'Rendered3 SVG,4 Mermaid;{len(tables)} analytical tables.')
