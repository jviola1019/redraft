from pathlib import Path
import re,html,json,csv,collections,io
ROOT=Path(__file__).resolve().parents[1];RAW=ROOT/'data/raw';OUT=ROOT/'data/processed'
def csvrows(name):return list(csv.DictReader(io.StringIO((RAW/name).read_text())))
def main():
 s=(RAW/'johnson_2014.html').read_text();table=re.findall(r'<table[^>]*>(.*?)</table>',s,re.S)[0];values={}
 for row in re.findall(r'<tr[^>]*>(.*?)</tr>',table,re.S)[1:]:
  cells=[html.unescape(re.sub('<[^>]+>','',x)).strip() for x in re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>',row,re.S)]
  for i in range(0,len(cells),2):
   if cells[i]:values[int(cells[i])]=float(cells[i+1].replace(',',''))
 assert set(values)==set(range(1,225));assert values[1]==3000 and values[224]==2
 result={'name':'Jimmy Johnson chart (49ers2014 publication)','source':'https://www.49ers.com/news/nfl-draft-value-chart-12850728','publishedAt':'2014-04-07T09:58:28Z','units':'Johnson chart points','licenseNote':'Functional numerical values extracted with attribution; no open article/prose/asset license asserted.','extension':'Picks225–256 are unpriced by original chart; gameValue=1 is a gameplay assumption, not historical fact.','values':[{'pick':i,'johnson':values.get(i),'gameValue':values.get(i,1),'basis':'published-chart' if i in values else 'gameplay-tail-extension'} for i in range(1,257)]}
 (OUT/'trade-values.json').write_text(json.dumps(result,indent=2));(ROOT/'data/clean/johnson-values.json').write_text(json.dumps(result,indent=2))
 groups=collections.defaultdict(list)
 for t in csvrows('trades.csv'):groups[t['trade_id']].append(t)
 windows={2013:('2013-04-25','2013-04-27'),2014:('2014-05-08','2014-05-10'),2015:('2015-04-30','2015-05-02'),2016:('2016-04-28','2016-04-30'),2017:('2017-04-27','2017-04-29'),2018:('2018-04-26','2018-04-28')};out=[]
 for y,(a,b) in windows.items():
  g=[v for v in groups.values() if a<=v[0]['trade_date']<=b];pure=[v for v in g if all(t['pick_season']==str(y) for t in v)];out.append({'year':y,'draftStart':a,'draftEnd':b,'distinctTradeIds':len(g),'pickRelatedTransactions':sum(any(t['pick_season'] for t in v) for v in g),'currentYearPicksOnly':len(pure),'assetRows':sum(len(v) for v in g)})
 report={'verifiedDate':'2026-11-02','source':'https://raw.githubusercontent.com/nflverse/nfldata/master/data/trades.csv','counts':out,'evaluationOnlyYear':2018,'notes':['Rows are assets; trade_id groups identify transactions.','PFR IDs on pick rows are eventual selection identities, not player assets.','Future pick overall numbers are retrospective and forbidden as contemporaneous estimates.','2018 includes39 transactions:38 involving picks and one player-only Switzer/Ward swap.','nfldata license not explicit; private research and derived aggregate counts only.','Counts are descriptive; CPU policy validation remains a separate empirical task.']};(ROOT/'data/clean/trade_frequency_research.json').write_text(json.dumps(report,indent=2));print(json.dumps({'chartValues':len(values),'tradeCounts':out},indent=2))
if __name__=='__main__':main()
