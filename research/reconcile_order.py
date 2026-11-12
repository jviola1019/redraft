"""Reverse actual draft-day transactions with audited source corrections."""
from pathlib import Path
import csv,collections,json,io,re
ROOT=Path(__file__).resolve().parents[1]
ALIAS={'GNB':'GB','KAN':'KC','NWE':'NE','NOR':'NO','SFO':'SF','TAM':'TB','SD':'LAC','SDG':'LAC','STL':'LAR','LA':'LAR','LV':'OAK','JAC':'JAX'}
def main():
 d=json.loads((ROOT/'data/processed/scenario-2018.json').read_text());state={p['overall']:p['team'] for p in d['actualPicks']};groups=collections.defaultdict(list)
 for r in csv.DictReader(io.StringIO((ROOT/'data/raw/trades.csv').read_text())):
  if '2018-04-26'<=r['trade_date']<='2018-04-28':groups[r['trade_id']].append(r)
 corrections=[{'tradeId':'1288','action':'Add omitted2018 pick255 TB toBUF','source':'https://www.buccaneers.com/news/bucs-swing-dramatic-first-round-trade-20586933','independentSource':'https://www.buffalobills.com/news/bills-trade-up-with-bucs-to-land-qb-josh-allen-20587262'},{'tradeId':'1291','action':'Correct2018 pick154 direction toBAL toBUF','source':'https://www.nfl.com/news/2018-nfl-draft-trade-tracker-details-of-all-the-moves-0ap3000000928057'}]
 # Revalidate facts in freshly downloaded primary-source body, not merely old assertions.
 assert '255' in (ROOT/'data/raw/correction_bucs_255.html').read_text()
 raw=(ROOT/'data/raw/trades_2018.html').read_text();a=json.loads(re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',raw,re.S)[0]);body=a['articleBody'];section=body[body.index('Bills beef up defense'):body.index('Saints make a big move')];assert section.index('154')<section.index('Ravens receive')
 assert not any(r['pick_number']=='255' for r in groups['1288'])
 groups['1288'].append({'trade_id':'1288','season':'2018','trade_date':'2018-04-26','gave':'TB','received':'BUF','pick_season':'2018','pick_round':'7','pick_number':'255','conditional':'0','pfr_id':'','pfr_name':''})
 found=[r for r in groups['1291'] if r['pick_number']=='154'];assert len(found)==1 and found[0]['gave']=='BUF' and found[0]['received']=='BAL';found[0]['gave']='BAL';found[0]['received']='BUF';errors=[]
 for k in sorted(groups,key=int,reverse=True):
  for r in groups[k]:
   if r['pick_season']!='2018':continue
   p=int(r['pick_number']);receiver=ALIAS.get(r['received'],r['received']);giver=ALIAS.get(r['gave'],r['gave'])
   if state[p]!=receiver:errors.append({'tradeId':k,'pick':p,'expected':receiver,'actual':state[p]})
   state[p]=giver
 diff=[{'pick':p['overall'],'official':p['owner'],'reconstructed':state[p['overall']]} for p in d['picks'] if p['owner']!=state[p['overall']]]
 oak=[p['overall'] for p in d['picks'] if p['owner']=='OAK'];assert oak==[10,41,75,110,159,173,185,212,216,217,228]
 report={'verifiedDate':'2026-11-02','method':'Reverse grouped draft-day asset transfers from actual final owners; compare with independently extracted official pre-draft order. Later results reconstruct past facts, not prospect ability.','sourceTransactions':len(groups),'pickRelatedTransactions':sum(any(r['pick_season'] for r in v) for v in groups.values()),'corrections':corrections,'assetOwnershipErrors':errors,'officialOrderDisagreements':diff,'matchedSlots':256-len(diff),'raidersApril20IndependentCheck':oak,'raidersSource':'https://static.clubs.nfl.com/image/upload/raiders/jcs5xnkdgnwwoglmp2rf.pdf','strictArchiveLimit':'Original per-field publication timestamps remain unavailable.'};(ROOT/'data/clean/order_reconciliation.json').write_text(json.dumps(report,indent=2));assert not errors and not diff;print(json.dumps(report,indent=2))
if __name__=='__main__':main()
