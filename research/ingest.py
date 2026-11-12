"""Fetch explicitly identified inputs; raw snapshots stay private and immutable by default."""
from pathlib import Path
import urllib.request,hashlib,json,datetime,concurrent.futures
ROOT=Path(__file__).resolve().parents[1]
SOURCES={
'draft_picks.csv':'https://github.com/nflverse/nflverse-data/releases/download/draft_picks/draft_picks.csv',
'combine.csv':'https://github.com/nflverse/nflverse-data/releases/download/combine/combine.csv',
'games.csv':'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv',
'order_2018.html':'https://www.nfl.com/news/2018-nfl-draft-order-for-all-seven-rounds-0ap3000000919673',
'license_nflverse.html':'https://github.com/nflverse',
'johnson_2014.html':'https://www.49ers.com/news/nfl-draft-value-chart-12850728',
'trades.csv':'https://raw.githubusercontent.com/nflverse/nfldata/master/data/trades.csv',
'trades_2018.html':'https://www.nfl.com/news/2018-nfl-draft-trade-tracker-details-of-all-the-moves-0ap3000000928057',
'raiders_2018_draft_release.pdf':'https://static.clubs.nfl.com/image/upload/raiders/jcs5xnkdgnwwoglmp2rf.pdf',
'roster_2017.csv':'https://github.com/nflverse/nflverse-data/releases/download/rosters/roster_2017.csv',
'depth_charts_2017.csv':'https://github.com/nflverse/nflverse-data/releases/download/depth_charts/depth_charts_2017.csv',
'dictionary_rosters.csv':'https://raw.githubusercontent.com/nflverse/nflreadr/main/data-raw/dictionary_rosters.csv',
'dictionary_depth_charts.csv':'https://raw.githubusercontent.com/nflverse/nflreadr/main/data-raw/dictionary_depth_charts.csv',
'correction_bucs_255.html':'https://www.buccaneers.com/news/bucs-swing-dramatic-first-round-trade-20586933',
'correction_bills_255.html':'https://www.buffalobills.com/news/bills-trade-up-with-bucs-to-land-qb-josh-allen-20587262',
'combine_invitees_2018.html':'https://www.neworleanssaints.com/news/nfl-releases-full-list-of-2018-combine-participants-20343293',
}
SOURCES.update({f'snap_counts_{y}.csv':f'https://github.com/nflverse/nflverse-data/releases/download/snap_counts/snap_counts_{y}.csv' for y in range(2012,2026)})

def fetch(item):
 name,url=item;p=ROOT/'data/raw'/name
 p.parent.mkdir(exist_ok=True,parents=True)
 if not p.exists():
  req=urllib.request.Request(url,headers={'User-Agent':'REDRAFT research source verification'})
  with urllib.request.urlopen(req,timeout=60) as response: b=response.read()
  p.write_bytes(b)
 b=p.read_bytes()
 return {'file':str(p.relative_to(ROOT)),'url':url,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'retrieved_at':datetime.datetime.fromtimestamp(p.stat().st_mtime,datetime.timezone.utc).isoformat()}
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex: manifest=list(ex.map(fetch,SOURCES.items()))
 for sub in ['raw','clean']:
  (ROOT/f'data/{sub}').mkdir(exist_ok=True,parents=True)
  (ROOT/f'data/{sub}/source_manifest.json').write_text(json.dumps(manifest,indent=2))
 print(json.dumps([{'file':m['file'],'bytes':m['bytes']} for m in manifest]))
