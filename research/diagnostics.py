"""Missingness, robust outliers and source coverage; never alters observations."""
from pathlib import Path
import csv,json,statistics,math,collections,io
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'data/clean'
def q(v,p):
 v=sorted(v);a=(len(v)-1)*p;lo=int(a);hi=math.ceil(a);return v[lo]+(v[hi]-v[lo])*(a-lo)
def main():
 data=json.loads((ROOT/'data/processed/scenario-2018.json').read_text());ps=[p for p in data['prospects'] if p['eligibilitySource']=='combine-participant'];fields=['heightIn','weightLb','forty','bench','verticalIn','broadJumpIn','cone','shuttle'];stats=[];flags=[];ranges={'heightIn':(60,85),'weightLb':(140,420),'forty':(3.9,6.5),'bench':(0,60),'verticalIn':(10,50),'broadJumpIn':(60,155),'cone':(5.5,10),'shuttle':(3.4,6.5)}
 for pos in sorted({p['position'] for p in ps}):
  group=[p for p in ps if p['position']==pos]
  for field in fields:
   values=[p[field] for p in group if p[field] is not None];missing=len(group)-len(values);entry={'position':pos,'field':field,'n':len(values),'missing':missing,'total':len(group),'missingFraction':missing/len(group)}
   if values:
    med=statistics.median(values);mad=statistics.median(abs(v-med) for v in values);entry.update({'min':min(values),'p25':q(values,.25),'median':med,'p75':q(values,.75),'max':max(values),'mad':mad})
    for p in group:
     v=p[field]
     if v is None:continue
     z=.67448975*(v-med)/mad if mad else 0;domain=not ranges[field][0]<=v<=ranges[field][1]
     if domain or(len(values)>=8 and abs(z)>3.5):flags.append({'prospectId':p['id'],'position':pos,'field':field,'value':v,'robustZ':z,'domainFailure':domain,'decision':'retain; statistical rarity alone does not establish measurement error'})
   stats.append(entry)
 report={'verifiedDate':'2026-11-02','datasetVersion':data['metadata']['version'],'population':'336 playable combine participants','rows':len(ps),'distributionByPosition':stats,'flaggedOutliers':flags,'nullPolicy':'Unknown measurement; unmeasured/not-reported reasons are not inferred. Null is never replaced by zero.','outlierPolicy':'MAD>3.5 within position when n>=8, or broad domain bounds. Review flags; no deletion or winsorization.'};(OUT/'distribution_diagnostics.json').write_text(json.dumps(report,indent=2))
 with (OUT/'missingness_by_prospect.csv').open('w') as f:
  w=csv.writer(f);w.writerow(['prospect_id','position']+fields)
  for p in ps:w.writerow([p['id'],p['position']]+[int(p[k] is None) for k in fields])
 snaps={};schedule=list(csv.DictReader(io.StringIO((ROOT/'data/raw/games.csv').read_text())))
 for year in range(2012,2026):
  rows=list(csv.DictReader(io.StringIO((ROOT/f'data/raw/snap_counts_{year}.csv').read_text())))
  actual={r['game_id'] for r in rows if r['game_type']=='REG'}
  expected={r['game_id'] for r in schedule if r['season']==str(year) and r['game_type']=='REG' and r['home_score']!='' and r['away_score']!=''}
  counts=collections.Counter((r['game_id'],r['pfr_player_id'],r['team']) for r in rows)
  snaps[year]={'rows':len(rows),'games':len({r['game_id'] for r in rows}),'regularGames':len(actual),'expectedCompletedRegularGames':len(expected),'missingScheduledRegularGames':sorted(expected-actual),'extraRegularGames':sorted(actual-expected),'missingPfrIds':sum(not r['pfr_player_id'] for r in rows),'duplicateGamePlayerTeamRows':sum(n-1 for n in counts.values() if n>1),'sourceStatus':'header-only-unavailable' if not rows else 'observed','allCompletedRegularGamesRepresented':actual==expected}
 (OUT/'snap_coverage.json').write_text(json.dumps(snaps,indent=2));print(json.dumps({'positionFieldGroups':len(stats),'outliersRetained':len(flags),'domainFailures':sum(x['domainFailure'] for x in flags),'snapCoverage':snaps},indent=2))
if __name__=='__main__':main()
