"""Audit2018 combine membership against a contemporaneous official team publication."""
from pathlib import Path
import re,html,csv,io,json,collections
ROOT=Path(__file__).resolve().parents[1]
def norm(s):return re.sub('[^a-z0-9]','',s.lower())
def school(s):
 s=norm(s)
 m={'louisianast':'lsu','jacksonvillestal':'jacksonvillestate','southernam':'southern','northcarolinaatst':'northcarolinaat','indianapenn':'indianapa','brighamyoung':'byu','southerncalifornia':'usc','texaschristian':'tcu','louisianalafayette':'louisiana','westmichigan':'westernmichigan','bostoncol':'bostoncollege','miamifla':'miami','miamifl':'miami','northcarolinast':'northcarolinastate','ncstate':'northcarolinastate','ncst':'northcarolinastate','connecticut':'uconn','mississippi':'olemiss','southernmississippi':'southernmiss','southernmethodist':'smu','texaselpaso':'utep','texassanantonio':'utsa'}
 s=m.get(s,s)
 if s.endswith('st'):s=s[:-2]+'state'
 return s
ALIASES={'davebright':'David Bright','darrencarrington':'Darren Carrington II','shaqgriffin':'Shaquem Griffin','desharrison':'Desmond Harrison','zayhenderson':'Zaycoven Henderson','mohurst':'Maurice Hurst','kamkelly':'Kameron Kelly','tjmartin':'Tavares Martin','kammoore':'Kamrin Moore','joenoteboom':'Joseph Noteboom','chennanwosu':'Uchenna Nwosu','chuksokorafor':'Chukwuma Okorafor','obookoronkwo':'Ogbonnia Okoronkwo','jakepugh':'Jacob Pugh','bunmirotimi':'Olubunmi Rotimi','jtthomas':'Jordan Thomas','trentthompson':'Trenton Thompson','lekauhatafe':'Salesi Uhatafe','cedwilson':'Cedrick Wilson'}
def main():
 text=(ROOT/'data/raw/combine_invitees_2018.html').read_text();table=re.findall(r'<table[^>]*>(.*?)</table>',text,re.S)[0];invitees=[]
 for row in re.findall(r'<tr[^>]*>(.*?)</tr>',table,re.S)[1:]:
  cells=[html.unescape(re.sub('<[^>]+>','',x)).strip() for x in re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>',row,re.S)];last,first=cells[1].split(',',1);invitees.append({'name':first.strip()+' '+last.strip(),'college':cells[2],'positionGroup':cells[4]})
 combine=[x for x in csv.DictReader(io.StringIO((ROOT/'data/raw/combine.csv').read_text())) if x['season']=='2018'];matched=[];unmatched=[]
 for i in invitees:
  key=norm(i['name']);target=ALIASES.get(key,i['name'])
  if key=='drewbrown' and school(i['college'])=='virginia':target='Andrew Brown'
  c=[x for x in combine if norm(x['player_name'])==norm(target) and school(x['school'])==school(i['college'])]
  if len(c)!=1:unmatched.append({**i,'candidateName':target,'candidates':[{'name':x['player_name'],'college':x['school']} for x in combine if norm(x['player_name'])==norm(target)]})
  else:matched.append({'officialName':i['name'],'officialCollege':i['college'],'combineName':c[0]['player_name'],'combineCollege':c[0]['school'],'method':'audited_alias_and_school' if norm(target)!=key else 'exact_normalized_name_and_school'})
 report={'verifiedDate':'2026-11-02','source':'https://www.neworleanssaints.com/news/nfl-releases-full-list-of-2018-combine-participants-20343293','officialCount':len(invitees),'datasetCount':len(combine),'matched':len(matched),'unmatched':unmatched,'matches':matched,'note':'Alias map is explicit and school-constrained. No fuzzy automatic joins. Two Drew Browns and two Jordan Thomases require college discrimination.'}
 (ROOT/'data/clean/eligibility_audit_2018.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='matches'},indent=2))
 assert len(matched)==336 and not unmatched
if __name__=='__main__':main()
